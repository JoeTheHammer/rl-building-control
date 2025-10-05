from typing import List

from fastapi import APIRouter
from fastapi.responses import FileResponse

from models.analytics import AnalyticsDataResponse, AnalyticsSuiteSummary
from services.analytics import get_suite_file_path, list_available_suites, load_suite_data


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
