"""API routes for exposing available controllers."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/controllers")
def get_controllers() -> JSONResponse:
    """Return the list of controllers exported by the testbed."""
    manifest_path = (
        Path(__file__).resolve().parents[3]
        / "testbed"
        / "manifest"
        / "controllers.json"
    )

    if not manifest_path.exists():
        raise HTTPException(status_code=500, detail="Controller manifest not found")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="Invalid controller manifest")
    return JSONResponse(content=data)
