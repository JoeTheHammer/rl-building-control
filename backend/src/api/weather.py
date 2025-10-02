from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter()

# Resolve path relative to project root (backend/)
BASE_DIR = Path(__file__).resolve().parents[3]
WEATHER_DIR = BASE_DIR / "data" / "environment" / "weather"

@router.get("/all")
def get_all_weather_folders():
    try:
        if not WEATHER_DIR.exists() or not WEATHER_DIR.is_dir():
            raise HTTPException(status_code=404, detail=f"Folder not found: {WEATHER_DIR}")

        ddy_files = []
        for folder in WEATHER_DIR.iterdir():
            if folder.is_dir():
                # collect all .ddy files in that folder
                for file in folder.glob("*.epw"):
                    ddy_files.append(f"{folder.name}/{file.name}")

        return {"epw_files": ddy_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
