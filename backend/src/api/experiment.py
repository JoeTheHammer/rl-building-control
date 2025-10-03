import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import yaml

from models.experiment import (
    ExperimentConfigDetailsResponse,
    ExperimentConfigSection,
    ExperimentLogResponse,
    ExperimentRunStatus,
    ExperimentSuiteResponse,
    RunExperimentSuiteRequest,
    SaveExperimentRequest,
    StopExperimentSuiteResponse,
)
from services.yaml_experiment import save_experiment_yaml
from services.experiment_suite import manager as suite_manager, resolve_config_path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = (BASE_DIR / "config" / "experiments").resolve()
ENVIRONMENTS_DIR = (BASE_DIR / "config" / "environments").resolve()
CONTROLLERS_DIR = (BASE_DIR / "config" / "controllers").resolve()


def _resolve_within(base: Path, name: str) -> Path:
    path = (base / name).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="Invalid configuration path") from exc
    return path


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if isinstance(data, dict):
        return data
    return {}


def _extract_config_filename(value: Optional[Any]) -> Optional[str]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return Path(stripped).name
    except (TypeError, ValueError):
        return stripped


def _resolve_related_config(
    content: Dict[str, Any],
    keys: List[str],
) -> Optional[str]:
    experiments = content.get("experiments")
    if isinstance(experiments, list):
        for experiment in experiments:
            if not isinstance(experiment, dict):
                continue
            for key in keys:
                if key in experiment:
                    filename = _extract_config_filename(experiment.get(key))
                    if filename:
                        return filename
    return None


def _build_section(path: Path) -> Optional[ExperimentConfigSection]:
    if not path.exists() or not path.is_file():
        return None
    try:
        content = _load_yaml_file(path)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ExperimentConfigSection(filename=path.name, content=content)


@router.post("/save")
def save_experiment(req: SaveExperimentRequest):
    try:
        filepath = EXPERIMENTS_DIR / req.filename
        save_experiment_yaml(req.experiments, filepath)
        return {"saved": True, "path": EXPERIMENTS_DIR / filepath.name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/all")
def get_all_experiment_configs():
    try:
        if not EXPERIMENTS_DIR.exists() or not EXPERIMENTS_DIR.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"Folder not found: {EXPERIMENTS_DIR}",
            )

        files = [f.name for f in EXPERIMENTS_DIR.glob("*.yaml")]
        return {"files": files}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/suites", response_model=List[ExperimentSuiteResponse])
def list_experiment_suites():
    return suite_manager.list_suites()


@router.post("/suites/run", response_model=ExperimentSuiteResponse)
def run_experiment_suite(req: RunExperimentSuiteRequest):
    config_path = resolve_config_path(req.config_name)
    return suite_manager.run_suite(req.suite_name, config_path)


@router.post("/suites/{suite_id}/stop", response_model=StopExperimentSuiteResponse)
def stop_experiment_suite(suite_id: int):
    suite = suite_manager.stop_suite(suite_id)
    return StopExperimentSuiteResponse(id=suite.id, status=suite.status)


@router.get(
    "/config-details/{config_name}",
    response_model=ExperimentConfigDetailsResponse,
)
def get_config_details(config_name: str):
    try:
        experiment_path = _resolve_within(EXPERIMENTS_DIR, config_name)
        if not experiment_path.exists() or not experiment_path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"Experiment config not found: {config_name}",
            )

        experiment_content = _load_yaml_file(experiment_path)
        experiment_section = ExperimentConfigSection(
            filename=experiment_path.name,
            content=experiment_content,
        )

        environment_filename = _resolve_related_config(
            experiment_content,
            ["environment_config", "environmentConfig"],
        )
        controller_filename = _resolve_related_config(
            experiment_content,
            ["controller_config", "controllerConfig"],
        )

        environment_section = (
            _build_section(_resolve_within(ENVIRONMENTS_DIR, environment_filename))
            if environment_filename
            else None
        )
        controller_section = (
            _build_section(_resolve_within(CONTROLLERS_DIR, controller_filename))
            if controller_filename
            else None
        )

        return ExperimentConfigDetailsResponse(
            experiment=experiment_section,
            environment=environment_section,
            controller=controller_section,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/suites/{suite_id}/status",
    response_model=ExperimentRunStatus,
)
def get_suite_status(suite_id: int):
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="Experiment suite path not available")

    status_path = Path(suite.path) / "status.yaml"
    if not status_path.exists() or not status_path.is_file():
        raise HTTPException(status_code=404, detail="Status file not available")

    try:
        data = _load_yaml_file(status_path)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    def _first_int(*keys: str) -> Optional[int]:
        for key in keys:
            value = data.get(key)
            if isinstance(value, int):
                return value
        return None

    return ExperimentRunStatus(
        status=data.get("status"),
        total_training_episodes=_first_int("total_training_episodes"),
        current_training_episode=_first_int("current_training_episode"),
        total_evaluation_episodes=_first_int(
            "total_evaluation_episodes", "total_evluation_episodes"
        ),
        current_evaluation_episode=_first_int("current_evaluation_episode"),
    )


@router.get(
    "/suites/{suite_id}/logs",
    response_model=ExperimentLogResponse,
)
def get_suite_logs(suite_id: int):
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="Experiment suite path not available")

    log_path = Path(suite.path) / "experiment_log.txt"
    if not log_path.exists() or not log_path.is_file():
        return ExperimentLogResponse(content="")

    try:
        with log_path.open("r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ExperimentLogResponse(content=content)


@router.get("/suites/{suite_id}/logs/stream")
async def stream_suite_logs(suite_id: int, request: Request):
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="Experiment suite path not available")

    log_path = Path(suite.path) / "experiment_log.txt"

    async def event_generator():
        last_position = 0
        buffer = ""
        while True:
            if await request.is_disconnected():
                break

            if log_path.exists() and log_path.is_file():
                try:
                    with log_path.open("r", encoding="utf-8", errors="ignore") as file:
                        file.seek(last_position)
                        chunk = file.read()
                        last_position = file.tell()
                except Exception as exc:  # pragma: no cover - defensive
                    raise HTTPException(status_code=500, detail=str(exc)) from exc

                if chunk:
                    combined = buffer + chunk
                    lines = combined.splitlines()
                    if combined and not combined.endswith("\n"):
                        buffer = lines.pop() if lines else combined
                    else:
                        buffer = ""

                    if lines:
                        payload = json.dumps({"lines": lines})
                        yield f"data: {payload}\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/{name}")
def get_experiment_config(name: str):
    try:
        file_path = EXPERIMENTS_DIR / name

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {name}")

        with file_path.open("r", encoding="utf-8") as file:
            content = yaml.safe_load(file)

        return {"name": name, "content": content}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))