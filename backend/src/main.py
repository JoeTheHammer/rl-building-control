from fastapi import FastAPI

from api import environment
from api import controller

app = FastAPI()

app.include_router(environment.router, prefix="/api/environment", tags=["environment"])
app.include_router(controller.router, prefix="/api/controller", tags=["controller"])
