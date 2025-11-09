import subprocess
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psutil

router = APIRouter()
SRC_DIR = Path(__file__).resolve().parents[1]

# Store active processes and their logs
_processes: dict[int, subprocess.Popen] = {}
_log_files: dict[int, any] = {}


class StartTestbed(BaseModel):
    config_path: str
    log_path: str
    work_dir: str


def _monitor_process(pid: int, process: subprocess.Popen, log_file) -> None:
    """Waits for process to finish and records exit status."""
    return_code = process.wait()
    log_file.close()

    status = "finished" if return_code == 0 else f"error ({return_code})"
    print(f"[Monitor] Process {pid} ended with status: {status}")

    # Remove from tracking dicts
    _processes.pop(pid, None)
    _log_files.pop(pid, None)

    # Optionally write result to a small file beside the log
    try:
        result_path = Path(log_file.name).with_suffix(".exit")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(status)
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
        if pid in _processes:
            p = _processes[pid]
            running = p.poll() is None
            if not running:
                return {"pid": pid, "status": "exited", "return_code": p.returncode}
            return {"pid": pid, "status": "running", "cmd": p.args}

        if not psutil.pid_exists(pid):
            # Check if an .exit file exists
            exit_file = Path(f"{pid}.exit")
            if exit_file.exists():
                return {
                    "pid": pid,
                    "status": exit_file.read_text().strip(),
                }
            return {"pid": pid, "status": "not running"}

        p = psutil.Process(pid)
        if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
            return {"pid": pid, "status": "not running"}

        return {"pid": pid, "status": "running", "cmd": p.cmdline()}

    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return {"pid": pid, "status": "not running"}

    except psutil.AccessDenied:
        return {"pid": pid, "status": "unknown"}


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
