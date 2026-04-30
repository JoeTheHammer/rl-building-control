from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from models.analytics import AnalyticsDataResponse, AnalyticsSuiteSummary
from models.experiment import ExperimentSuiteResponse, SuiteContextResponse
from services.experiment_context import (
    get_experiment_record_from_bytes,
    load_suite_context_from_bytes,
)
from services.experiment_suite import manager as suite_manager
from services.analytics import (
    get_suite_file_path,
    list_available_suites,
    load_suite_data,
    load_uploaded_hdf5_data,
)


router = APIRouter()


@router.get("/suites", response_model=List[AnalyticsSuiteSummary])
def get_suites() -> List[AnalyticsSuiteSummary]:
    return list_available_suites()


@router.get("/suites/{suite_id}/data", response_model=AnalyticsDataResponse)
def get_suite_data(suite_id: int) -> AnalyticsDataResponse:
    return load_suite_data(suite_id)


@router.get("/suites/{suite_id}/file")
def download_suite_file(suite_id: int) -> FileResponse:
    file_path = get_suite_file_path(suite_id)
    return FileResponse(
        path=file_path,
        media_type="application/x-hdf5",
        filename=file_path.name,
    )


@router.post("/file", response_model=AnalyticsDataResponse)
async def open_file(
    file: UploadFile = File(...),
    filename: str = Query(..., min_length=1),
) -> AnalyticsDataResponse:
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    if not filename.lower().endswith((".h5", ".hdf5")):
        raise HTTPException(status_code=400, detail="Only .h5 and .hdf5 files are supported")

    content = await file.read()
    return load_uploaded_hdf5_data(filename, content)


@router.post("/file/context", response_model=SuiteContextResponse)
async def open_file_context(
    file: UploadFile = File(...),
    filename: str = Query(..., min_length=1),
) -> SuiteContextResponse:
    if not filename.lower().endswith((".h5", ".hdf5")):
        raise HTTPException(status_code=400, detail="Only .h5 and .hdf5 files are supported")
    content = await file.read()
    return load_suite_context_from_bytes(filename, content)


@router.post("/file/experiments/{experiment_key}/reproduce", response_model=ExperimentSuiteResponse)
async def reproduce_uploaded_experiment(
    experiment_key: str,
    file: UploadFile = File(...),
    filename: str = Query(..., min_length=1),
    name: str | None = Query(None),
) -> ExperimentSuiteResponse:
    if not filename.lower().endswith((".h5", ".hdf5")):
        raise HTTPException(status_code=400, detail="Only .h5 and .hdf5 files are supported")
    content = await file.read()
    record = get_experiment_record_from_bytes(content, experiment_key)
    return suite_manager.reproduce_experiment_from_record(record, name)
