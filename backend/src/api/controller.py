from pathlib import Path
from fastapi import APIRouter, HTTPException

from models.controller import SaveControllerRequest
from services.yaml_controller import save_controller

router = APIRouter()

@router.post("/save")
def save_ctrl(req: SaveControllerRequest):
    try:
        filepath = Path(req.directory) / req.filename
        save_controller(req)  # this already writes the file
        return {"saved": True, "path": str(filepath.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
