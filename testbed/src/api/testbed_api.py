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

    env = os.environ.copy()
    env["PIPENV_PIPFILE"] = str(Path(__file__).resolve().parents[2] / "Pipfile")

    command = ["pipenv", "run", "python", str(main_py), str(request.config_path)]

    try:
        log_file = open(Path(request.log_path), "w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=request.work_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
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

        # Handle zombie processes
        if p.status() == psutil.STATUS_ZOMBIE:
            try:
                # Attempt to reap zombie if we're its parent
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass  # Not our child or already reaped
            return {"pid": pid, "status": "zombie - cleaned up"}

        # Process is alive and not a zombie
        return {"pid": pid, "status": "running", "cmd": p.cmdline()}

    except psutil.ZombieProcess:
        # Process is in zombie state (psutil detected it)
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass
        return {"pid": pid, "status": "zombie - cleaned up"}

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"pid": pid, "status": "not running"}


@router.post("/stop")
def stop():
    return {"Not implemented": "Not implemented"}
