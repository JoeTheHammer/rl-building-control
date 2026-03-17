import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import environment
from api import controller
from api import building
from api import weather
from api import experiment
from api import analytics

app = FastAPI()

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://138.232.66.68:5173",
]

configured_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
allow_origin_regex = os.getenv(
    "CORS_ALLOW_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|172\.\d+\.\d+\.\d+)(:\d+)?$",
)
allow_origins = sorted(set([*default_origins, *configured_origins]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(environment.router, prefix="/api/environment", tags=["environment"])
app.include_router(controller.router, prefix="/api/controller", tags=["controller"])
app.include_router(building.router, prefix="/api/building", tags=["building"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(experiment.router, prefix="/api/experiment", tags=["experiment"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
