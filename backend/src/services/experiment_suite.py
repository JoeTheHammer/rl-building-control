from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
from contextlib import contextmanager
from pathlib import Path
from threading import Lock, Thread
from typing import Dict, Iterable, Optional

from fastapi import HTTPException

from models.experiment import ExperimentSuiteResponse, ExperimentSuiteStatus

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "experiment_suites.db"
LOG_PATH = BASE_DIR / "experiment_log.txt"


class ExperimentSuiteRepository:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS experiment_suites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pid INTEGER
                )
                """
            )
            connection.commit()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def create(self, name: str, status: ExperimentSuiteStatus, pid: Optional[int]) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO experiment_suites (name, status, pid) VALUES (?, ?, ?)",
                (name, status.value if isinstance(status, ExperimentSuiteStatus) else status, pid),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_status(self, suite_id: int, status: ExperimentSuiteStatus, pid: Optional[int]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET status = ?, pid = ? WHERE id = ?",
                (status.value if isinstance(status, ExperimentSuiteStatus) else status, pid, suite_id),
            )
            connection.commit()

    def get(self, suite_id: int) -> Optional[ExperimentSuiteResponse]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, status, pid FROM experiment_suites WHERE id = ?",
                (suite_id,),
            ).fetchone()

        if row is None:
            return None

        return ExperimentSuiteResponse(
            id=int(row["id"]),
            name=str(row["name"]),
            status=str(row["status"]),
            pid=row["pid"],
        )

    def list(self) -> Iterable[ExperimentSuiteResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, status, pid FROM experiment_suites ORDER BY id DESC"
            ).fetchall()

        for row in rows:
            yield ExperimentSuiteResponse(
                id=int(row["id"]),
                name=str(row["name"]),
                status=str(row["status"]),
                pid=row["pid"],
            )


class ExperimentSuiteManager:
    def __init__(self) -> None:
        self._repository = ExperimentSuiteRepository()
        self._config_paths: Dict[int, Path] = {}
        self._processes: Dict[int, subprocess.Popen] = {}
        self._lock = Lock()

    def list_suites(self) -> list[ExperimentSuiteResponse]:
        return list(self._repository.list())

    def run_suite(self, name: str, config_path: Path) -> ExperimentSuiteResponse:
        testbed_path = os.getenv("TESTBED_PATH")
        if not testbed_path:
            raise HTTPException(status_code=500, detail="TESTBED_PATH environment variable is not set")

        src_path = Path(testbed_path).expanduser().resolve() / "src"
        if not src_path.exists():
            raise HTTPException(status_code=500, detail=f"Testbed src folder not found: {src_path}")

        full_config_path = config_path.expanduser().resolve()
        if not full_config_path.exists():
            raise HTTPException(status_code=404, detail=f"Experiment config not found: {full_config_path}")

        command = [
            "pipenv",
            "run",
            "python",
            "main.py",
            str(full_config_path),
        ]

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_file = open(LOG_PATH, "w", encoding="utf-8")

        try:
            process = subprocess.Popen(
                command,
                cwd=src_path,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as exc:
            log_file.close()
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        suite_id = self._repository.create(name, ExperimentSuiteStatus.RUNNING, process.pid)

        with self._lock:
            self._config_paths[suite_id] = full_config_path
            self._processes[suite_id] = process

        Thread(
            target=self._monitor_process,
            args=(suite_id, process, log_file),
            daemon=True,
        ).start()

        return ExperimentSuiteResponse(
            id=suite_id,
            name=name,
            status=ExperimentSuiteStatus.RUNNING.value,
            pid=process.pid,
        )

    def stop_suite(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")

        pid = suite.pid
        process: Optional[subprocess.Popen]
        with self._lock:
            process = self._processes.get(suite_id)

        if process is not None and process.poll() is None:
            process.terminate()
            process.wait()
        elif pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        self._repository.update_status(suite_id, ExperimentSuiteStatus.ABORTED, None)

        with self._lock:
            self._processes.pop(suite_id, None)

        return ExperimentSuiteResponse(
            id=suite_id,
            name=suite.name,
            status=ExperimentSuiteStatus.ABORTED.value,
            pid=None,
        )

    def _monitor_process(self, suite_id: int, process: subprocess.Popen, log_file) -> None:
        return_code = process.wait()
        log_file.close()

        status = (
            ExperimentSuiteStatus.FINISHED
            if return_code == 0
            else ExperimentSuiteStatus.ABORTED
        )
        pid: Optional[int] = None if status != ExperimentSuiteStatus.RUNNING else process.pid
        self._repository.update_status(suite_id, status, pid)

        with self._lock:
            self._processes.pop(suite_id, None)

    def resolve_config_path(self, config_name: str) -> Path:
        return (BASE_DIR / "config" / "experiments" / config_name).resolve()


manager = ExperimentSuiteManager()

