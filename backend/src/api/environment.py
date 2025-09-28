from pathlib import Path
from fastapi import APIRouter, HTTPException

from models.environment import SaveEnvironmentRequest
from services.yaml_env import save_environment_yaml

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
ENVIRONMENTS_DIR = BASE_DIR / "config" / "environments"

@router.post("/save")
def save_env(req: SaveEnvironmentRequest):
    try:
        filepath = Path(req.directory) / req.filename
        save_environment_yaml(req.config, filepath)
        return {"saved": True, "path": str(filepath.resolve())}
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