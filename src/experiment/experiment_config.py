from typing import List

from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    name: str
    engine: str
    environment_config: str
    controller: str
    controller_config: str


class ExperimentList(BaseModel):
    experiments: List[ExperimentConfig]
