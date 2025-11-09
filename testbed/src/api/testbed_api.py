import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psutil

router = APIRouter()
SRC_DIR = Path(__file__).resolve().parents[1]


class StartTestbed(BaseModel):
    config_path: str
    log_path: str
    work_dir: str


@router.post("/start")
def start(request: StartTestbed):
    main_py = SRC_DIR / "main.py"

    command = ["pipenv", "run", "python", str(main_py), str(request.config_path)]

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

    return {"pid": process.pid}


@router.get("/status/{pid}")
def get_status(pid: int):
    try:
        if not psutil.pid_exists(pid):
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
    try:
        if not psutil.pid_exists(pid):
            raise HTTPException(status_code=404, detail=f"Process {pid} not found")

        process = psutil.Process(pid)

        # Attempt graceful termination first
        process.terminate()
        try:
            process.wait(timeout=5)
            return {"pid": pid, "status": "terminated gracefully"}
        except psutil.TimeoutExpired:
            # Force kill if it didn't stop
            process.kill()
            return {"pid": pid, "status": "force killed"}

    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found")

    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied to terminate process {pid}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
