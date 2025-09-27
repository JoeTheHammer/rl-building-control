from pathlib import Path
from fastapi import APIRouter, HTTPException

from models.environment import SaveEnvironmentRequest
from services.yaml_env import save_environment_yaml

router = APIRouter()

@router.post("/save")
def save_env(req: SaveEnvironmentRequest):
    try:
        filepath = Path(req.directory) / req.filename
        save_environment_yaml(req.config, filepath)
        return {"saved": True, "path": str(filepath.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
