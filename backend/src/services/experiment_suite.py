from __future__ import annotations

import os
import re
import shutil
import signal
import sqlite3
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, Iterable, Optional, Set

import requests
import yaml

from fastapi import HTTPException

from models.experiment import ExperimentSuiteResponse, ExperimentSuiteStatus

PROJECT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_DIR / "data" / "experiments"
DB_PATH = BACKEND_DIR / "experiment_suites.db"

POLL_INTERVAL = 5


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
                    archived INTEGER NOT NULL DEFAULT 0,
                    tensorboard_enabled INTEGER NOT NULL DEFAULT 0
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
            if "tensorboard_enabled" not in column_names:
                connection.execute(
                    "ALTER TABLE experiment_suites ADD COLUMN tensorboard_enabled INTEGER NOT NULL DEFAULT 0"
                )

            connection.commit()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
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
        tensorboard_enabled: bool,
    ) -> int:
        with self._lock, self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO experiment_suites (
                    name,
                    status,
                    pid,
                    path,
                    config_filename,
                    archived,
                    tensorboard_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, status.value, pid, path, config_filename, 0, 1 if tensorboard_enabled else 0),
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
                """
                SELECT
                    id,
                    name,
                    status,
                    pid,
                    path,
                    config_filename,
                    archived,
                    tensorboard_enabled
                FROM experiment_suites
                WHERE id = ?
                """,
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
            tensorboard_enabled=bool(row["tensorboard_enabled"]),
        )

    def list(self) -> Iterable[ExperimentSuiteResponse]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    status,
                    pid,
                    path,
                    config_filename,
                    archived,
                    tensorboard_enabled
                FROM experiment_suites
                ORDER BY id DESC
                """
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
                tensorboard_enabled=bool(row["tensorboard_enabled"]),
            )

    def set_archived(self, suite_id: int, archived: bool) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET archived = ? WHERE id = ?",
                (1 if archived else 0, suite_id),
            )
            connection.commit()

    def set_tensorboard_enabled(self, suite_id: int, enabled: bool) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE experiment_suites SET tensorboard_enabled = ? WHERE id = ?",
                (1 if enabled else 0, suite_id),
            )
            connection.commit()

    def delete(self, suite_id: int) -> bool:
        with self._lock, self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM experiment_suites WHERE id = ?",
                (suite_id,),
            )
            connection.commit()
            return cursor.rowcount > 0


def resolve_config_path(config_name: str) -> Path:
    return (PROJECT_DIR / "config" / "experiments" / config_name).resolve()


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if isinstance(data, dict):
        return data
    return {}


def _resolve_controller_config_path(base_config: Path, controller_value: Any) -> Optional[Path]:
    if not isinstance(controller_value, str):
        return None
    raw = controller_value.strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = (base_config.parent / path).resolve()
    else:
        path = path.expanduser().resolve()
    return path if path.exists() and path.is_file() else None


def _controller_uses_tensorboard(path: Path) -> bool:
    try:
        content = _load_yaml_file(path)
    except Exception:
        return False

    training = content.get("training")
    if isinstance(training, dict) and training.get("tensorboard_logs") is True:
        return True

    hyperparameters = content.get("hyperparameters")
    if isinstance(hyperparameters, dict):
        value = hyperparameters.get("tensorboard_log")
        if isinstance(value, str) and value.strip():
            return True
        if bool(value) and value is not None:
            return True

    return False


def _detect_tensorboard_enabled(config_path: Path) -> bool:
    try:
        experiment_config = _load_yaml_file(config_path)
    except Exception:
        return False

    experiments = experiment_config.get("experiments")
    if not isinstance(experiments, list):
        return False

    for experiment in experiments:
        if not isinstance(experiment, dict):
            continue
        controller_value = experiment.get("controller_config") or experiment.get("controllerConfig")
        controller_path = _resolve_controller_config_path(config_path, controller_value)
        if controller_path and _controller_uses_tensorboard(controller_path):
            return True
    return False


class ExperimentSuiteManager:
    def __init__(self, repository: Optional[ExperimentSuiteRepository] = None) -> None:
        self._repository = repository or ExperimentSuiteRepository()
        self._config_paths: Dict[int, Path] = {}
        self._processes: Set[int] = set()
        self._lock = Lock()

    def list_suites(self) -> list[ExperimentSuiteResponse]:
        return list(self._repository.list())

    def get_suite(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")
        return suite

    def _initialize_suite(
        self,
        name: str,
        config_filename: str,
        tensorboard_enabled: bool,
    ) -> tuple[int, Path]:
        tmp_id = self._repository.create(
            name,
            ExperimentSuiteStatus.RUNNING,
            None,
            None,
            config_filename,
            tensorboard_enabled,
        )
        safe_name = _sanitize_name(name)
        suite_dir = DATA_DIR / f"experiment_{tmp_id}_{safe_name}"
        suite_dir.mkdir(parents=True, exist_ok=True)
        self._repository.update_path_and_filename(tmp_id, str(suite_dir), config_filename)
        return tmp_id, suite_dir

    def run_suite(self, name: str, config_path: Path) -> ExperimentSuiteResponse:
        """
        Starts a new experiment suite by calling the remote Testbed API.
        """
        PORT = 8001
        TESTBED_URL = f"http://127.0.0.1:{PORT}/api/testbed"
        START_URL = f"{TESTBED_URL}/start"

        full_config_path = config_path.expanduser().resolve()
        if not full_config_path.exists():
            raise HTTPException(status_code=404, detail=f"Experiment config not found: {full_config_path}")

        config_filename = full_config_path.name
        tensorboard_enabled = _detect_tensorboard_enabled(full_config_path)

        tmp_id, suite_dir = self._initialize_suite(name, config_filename, tensorboard_enabled)
        log_path = suite_dir / "experiment_log.txt"

        # Prepare JSON body for the testbed start API
        start_payload = {
            "config_path": str(full_config_path),
            "log_path": str(log_path),
            "work_dir": str(suite_dir),
        }

        try:
            response = requests.post(START_URL, json=start_payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=500, detail=f"Failed to start Testbed API: {exc}")

        data = response.json()
        pid = data.get("pid")
        if not isinstance(pid, int):
            raise HTTPException(status_code=500, detail=f"Unexpected response from Testbed API: {data}")

        # Update DB with PID
        self._repository.update_status(tmp_id, ExperimentSuiteStatus.RUNNING, pid)

        # Track the PID (not the process object)
        with self._lock:
            self._config_paths[tmp_id] = full_config_path
            self._processes.add(pid)  # store PID only

        # Monitor the testbed process remotely
        Thread(
            target=self._monitor_process,
            args=(tmp_id, pid, f"http://127.0.0.1:{PORT}"),
            daemon=True,
        ).start()

        return ExperimentSuiteResponse(
            id=tmp_id,
            name=name,
            status=ExperimentSuiteStatus.RUNNING,
            pid=pid,
            path=str(suite_dir),
            config_filename=config_filename,
            archived=False,
            tensorboard_enabled=tensorboard_enabled,
        )

    def reproduce_experiment(
            self,
            suite_id: int,
            experiment_key: str,
            name: Optional[str] = None,
    ) -> ExperimentSuiteResponse:
        """
        Reproduce an existing experiment by restoring its context and
        starting it via the remote Testbed API.
        """
        testbed_path = os.getenv("TESTBED_PATH")
        if not testbed_path:
            raise HTTPException(status_code=500, detail="TESTBED_PATH environment variable is not set")

        try:
            from services.experiment_context import get_experiment_record
        except ImportError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        record = get_experiment_record(suite_id, experiment_key)

        provided_name = (name or "").strip() if name is not None else ""
        base_name = (record.name or "").strip()
        default_name = f"Reproduction • {base_name}".strip(" •") if base_name else "Reproduction"
        reproduction_name = provided_name or default_name

        tmp_id, suite_dir = self._initialize_suite(
            reproduction_name,
            "context/configs/experiment.yaml",
            False,
        )

        context_dir = suite_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)

        # --- Recreate experiment context files ---
        def write_text_file(target_relative: str, content: str) -> Path:
            target_path = context_dir / Path(target_relative)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            return target_path

        def context_absolute_path(target_relative: str) -> str:
            return str((context_dir / Path(target_relative)).resolve())

        for resource in record.iter_resources():
            target = context_dir / Path(resource.relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(resource.content)

        environment_file = record.get_text_file("configs/environment.yaml")
        controller_file = record.get_text_file("configs/controller.yaml")
        entry_file = record.get_text_file("configs/experiment_entry.yaml")

        if environment_file is None:
            raise HTTPException(
                status_code=500,
                detail="Environment configuration is missing from the experiment export",
            )

        # --- Inject building/weather if present ---
        building_resource = None
        weather_resource = None
        for resource in record.iter_resources():
            rtype = resource.metadata.get("resource_type") if resource.metadata else None
            if rtype == "building_model":
                building_resource = resource
            elif rtype == "weather_epw":
                weather_resource = resource

        env_data = yaml.safe_load(environment_file.content.decode("utf-8")) or {}
        if building_resource:
            env_data["building_model"] = context_absolute_path(building_resource.relative_path)
        if weather_resource:
            env_data["weather_data"] = context_absolute_path(weather_resource.relative_path)

        environment_yaml = yaml.safe_dump(env_data, sort_keys=False, allow_unicode=True)
        environment_config_path = write_text_file(environment_file.relative_path, environment_yaml)

        controller_config_path = None
        if controller_file:
            controller_config_path = write_text_file(
                controller_file.relative_path, controller_file.content.decode("utf-8")
            )

        # --- Build new experiment YAML ---
        entry_data = yaml.safe_load(entry_file.content.decode("utf-8")) if entry_file else {}
        experiments_section = entry_data.get("experiments") if isinstance(entry_data, dict) else []
        experiment_definition = experiments_section[0] if experiments_section else {}

        experiment_definition["name"] = reproduction_name
        experiment_definition.pop("environmentConfig", None)
        experiment_definition.pop("controllerConfig", None)
        experiment_definition["environment_config"] = str(environment_config_path)
        if controller_config_path:
            experiment_definition["controller_config"] = str(controller_config_path)

        experiment_yaml_data = {"experiments": [experiment_definition]}
        config_path = write_text_file("configs/experiment.yaml",
                                      yaml.safe_dump(experiment_yaml_data, sort_keys=False, allow_unicode=True))

        tensorboard_enabled = _detect_tensorboard_enabled(config_path)
        self._repository.set_tensorboard_enabled(tmp_id, tensorboard_enabled)

        PORT = 8001
        TESTBED_URL = f"http://127.0.0.1:{PORT}/api/testbed/start"
        log_path = suite_dir / "experiment_log.txt"

        start_payload = {
            "config_path": str(config_path),
            "log_path": str(log_path),
            "work_dir": str(suite_dir),
        }

        try:
            response = requests.post(TESTBED_URL, json=start_payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=500, detail=f"Failed to start Testbed API: {exc}")

        data = response.json()
        pid = data.get("pid")
        if not isinstance(pid, int):
            raise HTTPException(status_code=500, detail=f"Unexpected response from Testbed API: {data}")

        # Update suite status in DB
        self._repository.update_status(tmp_id, ExperimentSuiteStatus.RUNNING, pid)

        with self._lock:
            self._config_paths[tmp_id] = config_path
            self._processes.add(pid)

        Thread(
            target=self._monitor_process,
            args=(tmp_id, pid, f"http://127.0.0.1:{PORT}"),
            daemon=True,
        ).start()

        return ExperimentSuiteResponse(
            id=tmp_id,
            name=reproduction_name,
            status=ExperimentSuiteStatus.RUNNING,
            pid=pid,
            path=str(suite_dir),
            config_filename="context/configs/experiment.yaml",
            archived=False,
            tensorboard_enabled=tensorboard_enabled,
        )

    def stop_suite(self, suite_id: int) -> ExperimentSuiteResponse:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")

        pid = suite.pid
        if not pid:
            raise HTTPException(status_code=400, detail="Suite has no running PID")

        TESTBED_URL = "http://127.0.0.1:8001/api/testbed/stop"

        try:
            response = requests.post(f"{TESTBED_URL}?pid={pid}", timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=500, detail=f"Failed to contact Testbed API: {exc}")

        self._repository.update_status(suite_id, ExperimentSuiteStatus.ABORTED, None)

        with self._lock:
            self._processes.discard(suite_id)

        return ExperimentSuiteResponse(
            id=suite_id,
            name=suite.name,
            status=ExperimentSuiteStatus.ABORTED,
            pid=None,
            path=suite.path,
            config_filename=suite.config_filename,
            archived=suite.archived,
            tensorboard_enabled=suite.tensorboard_enabled,
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

    def delete_suite(self, suite_id: int) -> None:
        suite = self._repository.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Experiment suite not found")

        if suite.status == ExperimentSuiteStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a running experiment suite",
            )

        if not suite.archived:
            raise HTTPException(
                status_code=400,
                detail="Only archived experiment suites can be deleted",
            )

        suite_path = suite.path
        directory_to_remove: Optional[Path] = None
        if suite_path:
            try:
                resolved = Path(suite_path).resolve()
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid experiment suite path",
                )

            try:
                resolved.relative_to(DATA_DIR)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Experiment suite path is outside the allowed directory",
                ) from exc

            if resolved.exists():
                directory_to_remove = resolved

        if directory_to_remove is not None:
            try:
                if directory_to_remove.is_dir():
                    shutil.rmtree(directory_to_remove)
                else:
                    directory_to_remove.unlink(missing_ok=True)
            except FileNotFoundError:
                pass
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete experiment suite data: {exc}",
                ) from exc

        deleted = self._repository.delete(suite_id)
        if not deleted:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Experiment suite not found")

    def _monitor_process(self, suite_id: int, pid: int, testbed_url: str) -> None:
        """
        Polls the remote Testbed container for the process status.
        When the process finishes, updates the suite status in DB.
        """
        while True:
            try:
                print(pid)
                response = requests.get(f"{testbed_url}/api/testbed/status/{pid}", timeout=5)
                data = response.json()
            except requests.RequestException as e:
                print(f"[WARN] Polling failed for suite {suite_id}: {e}")
                time.sleep(POLL_INTERVAL)
                continue

            status = data.get("status", "unknown")
            if status != "running":
                print(f"[INFO] Suite {suite_id} finished (PID {pid}, status={status})")

                current_suite = self._repository.get(suite_id)
                if current_suite and current_suite.status == ExperimentSuiteStatus.ABORTED.value:
                    print(f"[INFO] Suite {suite_id} already aborted; skipping overwrite.")
                    break

                final_status = (
                    ExperimentSuiteStatus.FINISHED
                    if status == "not running"
                    else ExperimentSuiteStatus.ABORTED
                )

                print(f"Updated with {final_status}")

                self._repository.update_status(suite_id, final_status, None)
                break

            time.sleep(POLL_INTERVAL)


manager = ExperimentSuiteManager()
