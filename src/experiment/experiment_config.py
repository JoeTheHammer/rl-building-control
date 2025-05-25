from typing import List, Literal, Union

from pydantic import BaseModel


class RandomRLControllerConfig(BaseModel):
    algorithm: Literal["random"]


ControllerConfig = Union[RandomRLControllerConfig]  # Just this one for now


class ExperimentConfig(BaseModel):
    name: str
    engine: str
    environment_config: str
    controller: ControllerConfig


class ExperimentList(BaseModel):
    experiments: List[ExperimentConfig]
