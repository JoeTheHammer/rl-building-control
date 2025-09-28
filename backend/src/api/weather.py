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

        folders = []
        for folder in WEATHER_DIR.iterdir():
            if folder.is_dir():
                has_ddy = any(file.suffix.lower() == ".ddy" for file in folder.iterdir())
                has_epw = any(file.suffix.lower() == ".epw" for file in folder.iterdir())
                if has_ddy and has_epw:
                    folders.append(folder.name)

        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
