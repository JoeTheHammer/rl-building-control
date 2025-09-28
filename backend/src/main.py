from fastapi import FastAPI

from api import environment
from api import controller
from api import building
from api import weather

app = FastAPI()

app.include_router(environment.router, prefix="/api/environment", tags=["environment"])
app.include_router(controller.router, prefix="/api/controller", tags=["controller"])
app.include_router(building.router, prefix="/api/building", tags=["building"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])