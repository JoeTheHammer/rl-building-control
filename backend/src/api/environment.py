from pathlib import Path
from fastapi import APIRouter, HTTPException
import yaml

from models.environment import SaveEnvironmentRequest
from services.yaml_env import save_environment_yaml

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
ENVIRONMENTS_DIR = BASE_DIR / "config" / "environments"

@router.post("/save")
def save_env(req: SaveEnvironmentRequest):
    try:
        # Store environment always to same path at the moment.
        filepath = ENVIRONMENTS_DIR / req.filename
        save_environment_yaml(req.config, filepath)
        return {"saved": True, "path": ENVIRONMENTS_DIR / filepath.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
def get_all_environment_configs():
    try:
        if not ENVIRONMENTS_DIR.exists() or not ENVIRONMENTS_DIR.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"Folder not found: {ENVIRONMENTS_DIR}"
            )

        files = [f.name for f in ENVIRONMENTS_DIR.glob("*.yaml")]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{name}")
def get_environment_config(name: str):
    try:
        file_path = ENVIRONMENTS_DIR / name

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {name}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        return {"name": name, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))