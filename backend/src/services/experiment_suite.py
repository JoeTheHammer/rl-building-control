from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
import re
from contextlib import contextmanager
from pathlib import Path
from threading import Lock, Thread
from typing import Dict, Iterable, Optional

from fastapi import HTTPException

from models.experiment import ExperimentSuiteResponse, ExperimentSuiteStatus

PROJECT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_DIR / "data" / "experiments"
DB_PATH = BACKEND_DIR / "experiment_suites.db"


def _sanitize_name(name: str) -> str:
    # replace spaces with underscore, drop unsafe chars
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip())
    return safe


class ExperimentSuiteRepository:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self.connect() as connection:
            # Ensure base table exists
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS experiment_suites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    path TEXT,
                    config_filename TEXT,
                    archived INTEGER NOT NULL DEFAULT 0
                )
            """
        )


            columns = connection.execute(
                "PRAGMA table_info(experiment_suites)"
            ).fetchall()
            column_names = {str(row["name"]) for row in columns}
            if "archived" not in column_names:
                connection.execute(
                    "ALTER TABLE experiment_suites ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )

            connection.commit()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def create(
        self,
        name: str,
        status: ExperimentSuiteStatus,
        pid: Optional[int],
        path: Optional[str],
        config_filename: Optional[str],
    ) -> int:
        with self._lock, self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO experiment_suites (name, status, pid, path, config_filename, archived) VALUES (?, ?, ?, ?, ?, ?)",
                (name, status.value, pid, path, config_filename, 0),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_status(self, suite_id: int, status: ExperimentSuiteStatus, pid: Optional[int]) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET status = ?, pid = ? WHERE id = ?",
                (status.value, pid, suite_id),
            )
            connection.commit()

    def update_path_and_filename(self, suite_id: int, path: str, config_filename: str) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET path = ?, config_filename = ? WHERE id = ?",
                (path, config_filename, suite_id),
            )
            connection.commit()

    def get(self, suite_id: int) -> Optional[ExperimentSuiteResponse]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, name, status, pid, path, config_filename, archived FROM experiment_suites WHERE id = ?",
                (suite_id,),
            ).fetchone()

        if row is None:
            return None

        return ExperimentSuiteResponse(
            id=int(row["id"]),
            name=str(row["name"]),
            status=row["status"],
            pid=row["pid"],
            path=row["path"],
            config_filename=row["config_filename"],
            archived=bool(row["archived"]),
        )

    def list(self) -> Iterable[ExperimentSuiteResponse]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, status, pid, path, config_filename, archived FROM experiment_suites ORDER BY id DESC"
            ).fetchall()

        for row in rows:
            yield ExperimentSuiteResponse(
                id=int(row["id"]),
                name=str(row["name"]),
                status=row["status"],
                pid=row["pid"],
                path=row["path"],
                config_filename=row["config_filename"],
                archived=bool(row["archived"]),
            )

    def set_archived(self, suite_id: int, archived: bool) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET archived = ? WHERE id = ?",
                (1 if archived else 0, suite_id),
            )
            connection.commit()


def resolve_config_path(config_name: str) -> Path:
    return (PROJECT_DIR / "config" / "experiments" / config_name).resolve()


class ExperimentSuiteManager:
    def __init__(self) -> None:
        self._repository = ExperimentSuiteRepository()
        self._config_paths: Dict[int, Path] = {}
        self._processes: Dict[int, subprocess.Popen] = {}
        self._lock = Lock()

    def list_suites(self) -> list[ExperimentSuiteResponse]:
        return list(self._repository.list())

    def get_suite(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")
        return suite

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

        config_filename = full_config_path.name

        # Step 1: Create DB entry with placeholder path
        tmp_id = self._repository.create(
            name, ExperimentSuiteStatus.RUNNING, None, None, config_filename
        )
        safe_name = _sanitize_name(name)
        suite_dir = DATA_DIR / f"experiment_{tmp_id}_{safe_name}"
        suite_dir.mkdir(parents=True, exist_ok=True)
        log_path = suite_dir / "experiment_log.txt"

        # Update DB with correct path + filename
        self._repository.update_path_and_filename(tmp_id, str(suite_dir), config_filename)

        main_py = src_path / "main.py"

        command = [
            "pipenv",
            "run",
            "python",
            str(main_py),
            str(full_config_path),
        ]

        # extend environment with PIPENV_PIPFILE pointing to the testbed
        env = os.environ.copy()
        env["PIPENV_PIPFILE"] = str(Path(testbed_path) / "Pipfile")

        try:
            log_file = open(log_path, "w", encoding="utf-8")
            process = subprocess.Popen(
                command,
                cwd=suite_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        # Step 2: Update DB with pid
        self._repository.update_status(tmp_id, ExperimentSuiteStatus.RUNNING, process.pid)

        # Step 3: Track process
        with self._lock:
            self._config_paths[tmp_id] = full_config_path
            self._processes[tmp_id] = process

        Thread(
            target=self._monitor_process,
            args=(tmp_id, process, log_file),
            daemon=True,
        ).start()

        return ExperimentSuiteResponse(
            id=tmp_id,
            name=name,
            status=ExperimentSuiteStatus.RUNNING,
            pid=process.pid,
            path=str(suite_dir),
            config_filename=config_filename,
            archived=False,
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
            status=ExperimentSuiteStatus.ABORTED,
            pid=None,
            path=suite.path,
            config_filename=suite.config_filename,
            archived=suite.archived,
        )

    def archive_suite(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")
        if suite.status == ExperimentSuiteStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail="Cannot archive a running experiment suite",
            )

        self._repository.set_archived(suite_id, True)
        updated = self._repository.get(suite_id)
        if updated is None:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Failed to archive experiment suite")
        return updated

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


manager = ExperimentSuiteManager()
