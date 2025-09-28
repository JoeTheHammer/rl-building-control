from pathlib import Path
from fastapi import APIRouter, HTTPException
import yaml

from models.controller import SaveControllerRequest
from services.yaml_controller import save_controller

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
CONTROLLERS_DIR = BASE_DIR / "config" / "controllers"

@router.post("/save")
def save_ctrl(req: SaveControllerRequest):
    try:
        filepath = Path(req.directory) / req.filename

        # Store controllers always to same dir at the moment.
        req.directory = str(CONTROLLERS_DIR)
        save_controller(req)
        return {"saved": True, "path": CONTROLLERS_DIR / filepath.name}
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


@router.get("/{name}")
def get_controller_config(name: str):
    try:
        file_path = CONTROLLERS_DIR / name

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {name}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        return {"name": name, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
