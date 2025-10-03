from __future__ import annotations

import os
import signal
import socket
import sqlite3
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, Iterable, Optional

from fastapi import HTTPException

from models.experiment import (
    ExperimentSuiteResponse,
    TensorBoardStatus,
    TensorBoardStatusResponse,
    StopTensorBoardResponse,
)
from services.experiment_suite import DB_PATH, ExperimentSuiteRepository


def _utcnow() -> datetime:
    return datetime.utcnow()


def _model_dump(model, **kwargs):
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)


@dataclass
class TensorBoardRecord:
    suite_id: int
    pid: Optional[int]
    port: Optional[int]
    logdir: str
    url: Optional[str]
    owner: Optional[str]
    status: str
    started_at: Optional[datetime]
    expires_at: Optional[datetime]
    updated_at: Optional[datetime]


class TensorBoardRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        with self.connect() as connection:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tensorboard_instances (
                    suite_id INTEGER PRIMARY KEY,
                    pid INTEGER,
                    port INTEGER,
                    logdir TEXT NOT NULL,
                    url TEXT,
                    owner TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    expires_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (suite_id) REFERENCES experiment_suites(id) ON DELETE CASCADE
                )
                """
            )

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
        finally:
            connection.close()

    def upsert(self, record: TensorBoardRecord) -> None:
        payload = (
            record.suite_id,
            record.pid,
            record.port,
            record.logdir,
            record.url,
            record.owner,
            record.status,
            record.started_at.isoformat() if record.started_at else None,
            record.expires_at.isoformat() if record.expires_at else None,
            _utcnow().isoformat(),
        )
        with self._lock, self.connect() as connection:
            connection.execute(
                """
                INSERT INTO tensorboard_instances (
                    suite_id, pid, port, logdir, url, owner, status, started_at, expires_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(suite_id) DO UPDATE SET
                    pid=excluded.pid,
                    port=excluded.port,
                    logdir=excluded.logdir,
                    url=excluded.url,
                    owner=excluded.owner,
                    status=excluded.status,
                    started_at=excluded.started_at,
                    expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
                """,
                payload,
            )
            connection.commit()

    def mark_stopped(self, suite_id: int, expected_pid: Optional[int] = None) -> None:
        query = (
            "UPDATE tensorboard_instances "
            "SET status = ?, pid = NULL, port = NULL, url = NULL, expires_at = NULL, updated_at = ? "
            "WHERE suite_id = ?"
        )
        params: list[Any] = ["stopped", _utcnow().isoformat(), suite_id]
        if expected_pid is not None:
            query += " AND (pid = ? OR pid IS NULL)"
            params.append(expected_pid)

        with self._lock, self.connect() as connection:
            connection.execute(query, tuple(params))
            connection.commit()

    def get(self, suite_id: int) -> Optional[TensorBoardRecord]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT suite_id, pid, port, logdir, url, owner, status, started_at, expires_at, updated_at "
                "FROM tensorboard_instances WHERE suite_id = ?",
                (suite_id,),
            ).fetchone()

        if row is None:
            return None

        return TensorBoardRecord(
            suite_id=int(row["suite_id"]),
            pid=row["pid"],
            port=row["port"],
            logdir=str(row["logdir"]),
            url=row["url"],
            owner=row["owner"],
            status=str(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )

    def list(self) -> Iterable[TensorBoardRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT suite_id, pid, port, logdir, url, owner, status, started_at, expires_at, updated_at FROM tensorboard_instances"
            ).fetchall()

        for row in rows:
            yield TensorBoardRecord(
                suite_id=int(row["suite_id"]),
                pid=row["pid"],
                port=row["port"],
                logdir=str(row["logdir"]),
                url=row["url"],
                owner=row["owner"],
                status=str(row["status"]),
                started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            )


class TensorBoardManager:
    HOST = "127.0.0.1"
    DEFAULT_TTL = timedelta(hours=1)
    REAPER_INTERVAL = 60
    STOP_TIMEOUT = 10

    def __init__(self, repository: Optional[ExperimentSuiteRepository] = None) -> None:
        self._suite_repository = repository or ExperimentSuiteRepository()
        self._repository = TensorBoardRepository()
        self._processes: Dict[int, subprocess.Popen] = {}
        self._lock = Lock()
        self._log_files: Dict[int, Any] = {}

        self._cleanup_stale_records()
        Thread(target=self._reaper_loop, daemon=True).start()

    def _cleanup_stale_records(self) -> None:
        for record in self._repository.list():
            if record.status != "running":
                continue
            if not record.pid or not self._is_process_alive(record.pid):
                self._repository.mark_stopped(record.suite_id, expected_pid=record.pid)

    def _reaper_loop(self) -> None:
        while True:
            time.sleep(self.REAPER_INTERVAL)
            for record in self._repository.list():
                if record.status != "running":
                    continue
                if not record.pid or not self._is_process_alive(record.pid):
                    self._repository.mark_stopped(record.suite_id, expected_pid=record.pid)
                    continue
                if record.expires_at and record.expires_at <= _utcnow():
                    try:
                        self.stop(record.suite_id)
                    except HTTPException:
                        pass

    def _is_process_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def _allocate_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.HOST, 0))
            return int(sock.getsockname()[1])

    def _close_log_file(self, suite_id: int) -> None:
        with self._lock:
            handle = self._log_files.pop(suite_id, None)
        if handle and not handle.closed:
            try:
                handle.close()
            except Exception:
                pass

    def _track_process(self, suite_id: int, process: subprocess.Popen) -> None:
        def _runner() -> None:
            process.wait()
            with self._lock:
                stored = self._processes.get(suite_id)
                if stored is process:
                    self._processes.pop(suite_id, None)
            self._close_log_file(suite_id)
            self._repository.mark_stopped(suite_id, expected_pid=process.pid)

        Thread(target=_runner, daemon=True).start()

    def _ensure_suite_available(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._suite_repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")
        return suite

    def _build_status(
        self,
        suite: ExperimentSuiteResponse,
        record: Optional[TensorBoardRecord],
    ) -> TensorBoardStatusResponse:
        running = False
        url: Optional[str] = None
        port: Optional[int] = None
        pid: Optional[int] = None
        owner: Optional[str] = None
        started_at: Optional[datetime] = None
        expires_at: Optional[datetime] = None

        if suite.tensorboard_enabled and record:
            if record.status == "running" and record.pid and self._is_process_alive(record.pid):
                running = True
                url = record.url
                port = record.port
                pid = record.pid
                owner = record.owner
                started_at = record.started_at
                expires_at = record.expires_at
            elif record.status == "running":
                self._repository.mark_stopped(suite.id, expected_pid=record.pid)

        return TensorBoardStatusResponse(
            suite_id=suite.id,
            enabled=suite.tensorboard_enabled,
            running=running,
            url=url,
            port=port,
            pid=pid,
            owner=owner,
            started_at=started_at,
            expires_at=expires_at,
        )

    def enrich_suite(self, suite: ExperimentSuiteResponse) -> ExperimentSuiteResponse:
        status = self.status_for_suite(suite)
        status_payload = _model_dump(status, exclude={"suite_id"})
        tensorboard = TensorBoardStatus(**status_payload)
        update = {"tensorboard": tensorboard}
        if hasattr(suite, "model_copy"):
            return suite.model_copy(update=update)
        return suite.copy(update=update)

    def status(self, suite_id: int) -> TensorBoardStatusResponse:
        suite = self._ensure_suite_available(suite_id)
        record = self._repository.get(suite_id)
        return self._build_status(suite, record)

    def status_for_suite(self, suite: ExperimentSuiteResponse) -> TensorBoardStatusResponse:
        record = self._repository.get(suite.id)
        return self._build_status(suite, record)

    def start(self, suite_id: int, owner: Optional[str] = None) -> TensorBoardStatusResponse:
        suite = self._ensure_suite_available(suite_id)
        if not suite.tensorboard_enabled:
            raise HTTPException(status_code=400, detail="TensorBoard was not enabled for this suite")
        if not suite.path:
            raise HTTPException(status_code=400, detail="Experiment suite path not available")

        record = self._repository.get(suite_id)
        if record and record.status == "running" and record.pid and self._is_process_alive(record.pid):
            return self._build_status(suite, record)

        if record and record.status == "running":
            self._repository.mark_stopped(suite_id, expected_pid=record.pid)

        log_dir = Path(suite.path) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        testbed_path = os.getenv("TESTBED_PATH")
        if not testbed_path:
            raise HTTPException(status_code=500, detail="TESTBED_PATH environment variable is not set")

        port = self._allocate_port()
        url = f"http://{self.HOST}:{port}/"

        command = [
            "pipenv",
            "run",
            "tensorboard",
            f"--logdir={log_dir}",
            f"--host={self.HOST}",
            f"--port={port}",
        ]

        env = os.environ.copy()
        env["PIPENV_PIPFILE"] = str(Path(testbed_path) / "Pipfile")

        log_file_path = Path(suite.path) / "tensorboard.log"
        log_file = open(log_file_path, "w", encoding="utf-8")

        try:
            process = subprocess.Popen(
                command,
                cwd=Path(suite.path),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
            )
        except FileNotFoundError as exc:
            log_file.close()
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        with self._lock:
            self._processes[suite_id] = process
            self._log_files[suite_id] = log_file

        started_at = _utcnow()
        expires_at = started_at + self.DEFAULT_TTL

        self._repository.upsert(
            TensorBoardRecord(
                suite_id=suite_id,
                pid=process.pid,
                port=port,
                logdir=str(log_dir),
                url=url,
                owner=owner or "api",
                status="running",
                started_at=started_at,
                expires_at=expires_at,
                updated_at=started_at,
            )
        )

        self._track_process(suite_id, process)

        return self._build_status(suite, self._repository.get(suite_id))

    def stop(self, suite_id: int) -> StopTensorBoardResponse:
        suite = self._ensure_suite_available(suite_id)
        record = self._repository.get(suite_id)

        if not record or record.status != "running":
            status = self._build_status(suite, record)
            payload = _model_dump(status)
            payload["stopped"] = not status.running
            return StopTensorBoardResponse(**payload)

        terminated = False

        with self._lock:
            process = self._processes.pop(suite_id, None)

        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=self.STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            finally:
                terminated = True
        elif record.pid:
            try:
                os.kill(record.pid, signal.SIGTERM)
                end_time = time.time() + self.STOP_TIMEOUT
                while time.time() < end_time:
                    if not self._is_process_alive(record.pid):
                        break
                    time.sleep(0.2)
                else:
                    os.kill(record.pid, signal.SIGKILL)
                terminated = True
            except ProcessLookupError:
                terminated = True

        self._close_log_file(suite_id)
        self._repository.mark_stopped(suite_id, expected_pid=record.pid)

        status = self._build_status(suite, self._repository.get(suite_id))
        payload = _model_dump(status)
        payload["stopped"] = terminated or not status.running
        return StopTensorBoardResponse(**payload)


_shared_repository = ExperimentSuiteRepository()
tensorboard_manager = TensorBoardManager(repository=_shared_repository)
