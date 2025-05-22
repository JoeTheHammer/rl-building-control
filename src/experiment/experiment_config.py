from typing import List

from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    """
    Represents a single experiment configuration.
    """
    name: str
    engine: str
    environment_config: str


class ExperimentList(BaseModel):
    """
    Represents a list of experiments loaded from a config file.
    """
    experiments: List[ExperimentConfig]
