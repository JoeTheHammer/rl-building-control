from pathlib import Path

from fastapi import APIRouter, HTTPException
import yaml

from models.experiment import SaveExperimentRequest
from services.yaml_experiment import save_experiment_yaml

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
