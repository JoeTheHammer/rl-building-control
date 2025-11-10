import subprocess
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psutil
import json


router = APIRouter()
SRC_DIR = Path(__file__).resolve().parents[1]

# Store active processes and their logs
_processes: dict[int, subprocess.Popen] = {}
_log_files: dict[int, any] = {}

_exit_info: dict[int, dict[str, int | str | None]] = {}


class StartTestbed(BaseModel):
    config_path: str
    log_path: str
    work_dir: str


def _monitor_process(pid: int, process: subprocess.Popen, log_file) -> None:
    """Waits for process to finish and records exit status."""
    return_code = process.wait()
    log_file.close()

    status = "finished" if return_code == 0 else "error"
    print(f"[Monitor] Process {pid} ended with status: {status} ({return_code})")

    # Remove from tracking dicts
    _processes.pop(pid, None)
    _log_files.pop(pid, None)

    # Store result in memory
    _exit_info[pid] = {"status": status, "return_code": return_code}

    # (optional) also write to file for persistence
    try:
        result_path = Path(log_file.name).with_suffix(".exit.json")
        result_data = {"status": status, "return_code": return_code}
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f)
    except Exception:
        pass



@router.post("/start")
def start(request: StartTestbed):
    """Starts a new testbed process and logs its output."""
    main_py = SRC_DIR / "main.py"
    command = ["python", str(main_py), str(request.config_path)]

    try:
        log_file = open(Path(request.log_path), "w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=request.work_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _processes[process.pid] = process
    _log_files[process.pid] = log_file

    # Start monitoring thread
    thread = threading.Thread(
        target=_monitor_process, args=(process.pid, process, log_file), daemon=True
    )
    thread.start()

    return {"pid": process.pid}


@router.get("/status/{pid}")
def get_status(pid: int):
    """Checks whether a given process is running or has exited."""
    try:
        # Check if still tracked
        if pid in _processes:
            p = _processes[pid]
            running = p.poll() is None
            if not running:
                return {
                    "pid": pid,
                    "status": "exited",
                    "return_code": p.returncode,
                }
            return {"pid": pid, "status": "running", "cmd": p.args}

        # Check if we have exit info in memory
        if pid in _exit_info:
            info = _exit_info[pid]
            return {
                "pid": pid,
                "status": info["status"],
                "return_code": info["return_code"],
            }

        # Check if process exists in the OS
        if not psutil.pid_exists(pid):
            return {"pid": pid, "status": "not running", "return_code": None}

        p = psutil.Process(pid)
        if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
            return {"pid": pid, "status": "not running", "return_code": None}

        return {"pid": pid, "status": "running", "cmd": p.cmdline()}

    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return {"pid": pid, "status": "not running", "return_code": None}
    except psutil.AccessDenied:
        return {"pid": pid, "status": "unknown", "return_code": None}



@router.post("/stop")
def stop(pid: int):
    """Attempts to terminate or kill the process."""
    try:
        process = _processes.get(pid)
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
                return {"pid": pid, "status": "terminated gracefully"}
            except subprocess.TimeoutExpired:
                process.kill()
                return {"pid": pid, "status": "force killed"}
        else:
            if not psutil.pid_exists(pid):
                raise HTTPException(status_code=404, detail=f"Process {pid} not found")

            p = psutil.Process(pid)
            p.terminate()
            try:
                p.wait(timeout=5)
                return {"pid": pid, "status": "terminated gracefully"}
            except psutil.TimeoutExpired:
                p.kill()
                return {"pid": pid, "status": "force killed"}

    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found")

    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied to terminate process {pid}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
