from pathlib import Path
from fastapi import APIRouter, HTTPException

from models.controller import SaveControllerRequest
from services.yaml_controller import save_controller

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
CONTROLLERS_DIR = BASE_DIR / "config" / "controllers"

@router.post("/save")
def save_ctrl(req: SaveControllerRequest):
    try:
        filepath = Path(req.directory) / req.filename
        save_controller(req)
        return {"saved": True, "path": str(filepath.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
def get_all_controller_configs():
    try:
        if not CONTROLLERS_DIR.exists() or not CONTROLLERS_DIR.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"Folder not found: {CONTROLLERS_DIR}"
            )

        files = [f.name for f in CONTROLLERS_DIR.glob("*.yaml")]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))