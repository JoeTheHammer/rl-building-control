from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter()

# Resolve path relative to project root
BASE_DIR = Path(__file__).resolve().parents[3]   # points to backend/
DATA_DIR = BASE_DIR / "data" / "environment" / "buildings"

@router.get("/all")
def get_all_building_model_files():
    try:
        if not DATA_DIR.exists() or not DATA_DIR.is_dir():
            raise HTTPException(status_code=404, detail=f"Folder not found: {DATA_DIR}")

        files = [f.name for f in DATA_DIR.glob("*.epJSON")] 
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
