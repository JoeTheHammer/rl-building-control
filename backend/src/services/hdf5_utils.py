from pathlib import Path

from fastapi import HTTPException


def find_latest_h5_file(directory: Path) -> Path:
    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=404, detail="Experiment suite directory not found")

    candidates = sorted(directory.glob("*.h5"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(status_code=404, detail="No HDF5 export found for the selected suite")
    return candidates[0]
