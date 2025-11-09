from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import testbed_api


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(testbed_api.router, prefix="/api/testbed", tags=["testbed"])
