from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import environment
from api import controller
from api import building
from api import weather
from api import experiment
from api import analytics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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