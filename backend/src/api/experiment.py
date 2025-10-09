import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import yaml

from models.experiment import (
    ExperimentConfigDetailsExperiment,
    ExperimentConfigDetailsResponse,
    ExperimentConfigSection,
    ExperimentLogResponse,
    ExperimentProgress,
    ExperimentRunStatus,
    ExperimentSuiteResponse,
    RunExperimentSuiteRequest,
    SaveExperimentRequest,
    StopExperimentSuiteResponse,
    StartTensorBoardRequest,
    StopTensorBoardRequest,
    TensorBoardStatusResponse,
    StopTensorBoardResponse,
)
from services.yaml_experiment import save_experiment_yaml
from services.experiment_suite import manager as suite_manager, resolve_config_path
from services.tensorboard import tensorboard_manager

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = (BASE_DIR / "config" / "experiments").resolve()
ENVIRONMENTS_DIR = (BASE_DIR / "config" / "environments").resolve()
CONTROLLERS_DIR = (BASE_DIR / "config" / "controllers").resolve()

LEGACY_REPORTING_FIELDS = {"plots", "export"}


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
        return _remove_legacy_reporting_fields(data)
    return {}


def _remove_legacy_reporting_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    experiments = data.get("experiments")
    if not isinstance(experiments, list):
        return data

    for experiment in experiments:
        if not isinstance(experiment, dict):
            continue
        reporting = experiment.get("reporting")
        if not isinstance(reporting, dict):
            continue
        for field in LEGACY_REPORTING_FIELDS:
            reporting.pop(field, None)

    return data


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


def _get_experiment_value(experiment: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if key in experiment:
            return experiment.get(key)
    return None


def _build_experiment_sections(
    content: Dict[str, Any],
) -> List[ExperimentConfigDetailsExperiment]:
    experiments = content.get("experiments")
    if not isinstance(experiments, list):
        return []

    entries: List[ExperimentConfigDetailsExperiment] = []
    for index, experiment in enumerate(experiments, start=1):
        if not isinstance(experiment, dict):
            continue

        name_value = experiment.get("name")
        name = name_value if isinstance(name_value, str) else None

        environment_raw = _get_experiment_value(
            experiment, "environment_config", "environmentConfig"
        )
        controller_raw = _get_experiment_value(
            experiment, "controller_config", "controllerConfig"
        )

        environment_filename = _extract_config_filename(environment_raw)
        controller_filename = _extract_config_filename(controller_raw)

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

        entries.append(
            ExperimentConfigDetailsExperiment(
                id=index,
                name=name,
                environment=environment_section,
                controller=controller_section,
                environment_path=str(environment_raw)
                if isinstance(environment_raw, str)
                else environment_filename,
                controller_path=str(controller_raw)
                if isinstance(controller_raw, str)
                else controller_filename,
            )
        )

    return entries


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
        full_paths = EXPERIMENTS_DIR.glob("*.yaml")
        return {"files": files, "fullPaths": full_paths}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/suites", response_model=List[ExperimentSuiteResponse])
def list_experiment_suites():
    suites = suite_manager.list_suites()
    return [tensorboard_manager.enrich_suite(suite) for suite in suites]


@router.post("/suites/run", response_model=ExperimentSuiteResponse)
def run_experiment_suite(req: RunExperimentSuiteRequest):
    config_path = resolve_config_path(req.config_name)
    suite = suite_manager.run_suite(req.suite_name, config_path)
    return tensorboard_manager.enrich_suite(suite)


@router.post("/suites/{suite_id}/stop", response_model=StopExperimentSuiteResponse)
def stop_experiment_suite(suite_id: int):
    suite = suite_manager.stop_suite(suite_id)
    try:
        tensorboard_manager.stop(suite_id)
    except HTTPException:
        pass
    return StopExperimentSuiteResponse(id=suite.id, status=suite.status)


@router.post("/suites/{suite_id}/archive", response_model=ExperimentSuiteResponse)
def archive_experiment_suite(suite_id: int):
    suite = suite_manager.archive_suite(suite_id)
    return tensorboard_manager.enrich_suite(suite)


@router.delete("/suites/{suite_id}")
def delete_experiment_suite(suite_id: int):
    suite_manager.delete_suite(suite_id)
    return {"deleted": True}


@router.get(
    "/suites/{suite_id}/tensorboard",
    response_model=TensorBoardStatusResponse,
)
def get_tensorboard_status(suite_id: int):
    return tensorboard_manager.status(suite_id)


@router.post(
    "/suites/{suite_id}/tensorboard/start",
    response_model=TensorBoardStatusResponse,
)
def start_tensorboard(suite_id: int, payload: StartTensorBoardRequest | None = None):
    owner = payload.owner if payload else None
    return tensorboard_manager.start(suite_id, owner=owner)


@router.post(
    "/suites/{suite_id}/tensorboard/stop",
    response_model=StopTensorBoardResponse,
)
def stop_tensorboard(
    suite_id: int,
    payload: StopTensorBoardRequest | None = None,  # noqa: ARG001 - accepted for sendBeacon payloads
):
    return tensorboard_manager.stop(suite_id)


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

        experiment_sections = _build_experiment_sections(experiment_content)
        first_section = experiment_sections[0] if experiment_sections else None
        environment_section = first_section.environment if first_section else None
        controller_section = first_section.controller if first_section else None

        return ExperimentConfigDetailsResponse(
            experiment=experiment_section,
            environment=environment_section,
            controller=controller_section,
            experiments=experiment_sections,
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

    def _as_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    experiments_data = data.get("experiments")
    experiments: List[ExperimentProgress] = []

    if isinstance(experiments_data, list):
        for item in experiments_data:
            if not isinstance(item, dict):
                continue
            experiment_id = _as_int(item.get("id"))
            if experiment_id is None:
                continue
            experiments.append(
                ExperimentProgress(
                    id=experiment_id,
                    name=item.get("name") if isinstance(item.get("name"), str) else None,
                    status=item.get("status") if isinstance(item.get("status"), str) else None,
                    total_training_episodes=_as_int(
                        item.get("total_training_episodes")
                    ),
                    current_training_episode=_as_int(
                        item.get("current_training_episode")
                    ),
                    total_evaluation_episodes=_as_int(
                        item.get("total_evaluation_episodes")
                        if item.get("total_evaluation_episodes") is not None
                        else item.get("total_evluation_episodes")
                    ),
                    current_evaluation_episode=_as_int(
                        item.get("current_evaluation_episode")
                    ),
                )
            )
    else:
        # Fallback for legacy status files without per-experiment data
        total_training = _as_int(data.get("total_training_episodes"))
        current_training = _as_int(data.get("current_training_episode"))
        total_evaluation = _as_int(
            data.get("total_evaluation_episodes")
            if data.get("total_evaluation_episodes") is not None
            else data.get("total_evluation_episodes")
        )
        current_evaluation = _as_int(data.get("current_evaluation_episode"))
        legacy_status = data.get("status")
        if (
            legacy_status
            or total_training is not None
            or current_training is not None
            or total_evaluation is not None
            or current_evaluation is not None
        ):
            experiments.append(
                ExperimentProgress(
                    id=1,
                    status=legacy_status if isinstance(legacy_status, str) else None,
                    total_training_episodes=total_training,
                    current_training_episode=current_training,
                    total_evaluation_episodes=total_evaluation,
                    current_evaluation_episode=current_evaluation,
                )
            )

    experiments.sort(key=lambda item: item.id)
    return ExperimentRunStatus(experiments=experiments)


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