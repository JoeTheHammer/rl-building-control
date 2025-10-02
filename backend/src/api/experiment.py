from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
import yaml

from models.experiment import (
    ExperimentSuiteResponse,
    RunExperimentSuiteRequest,
    SaveExperimentRequest,
    StopExperimentSuiteResponse,
)
from services.yaml_experiment import save_experiment_yaml
from services.experiment_suite import manager as suite_manager

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
EXPERIMENTS_DIR = BASE_DIR / "config" / "experiments"


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
