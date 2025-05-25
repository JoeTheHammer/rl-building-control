from typing import List, Optional

from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    name: str
    engine: str
    environment_config: str
    controller: str
    controller_config: Optional[str] = None


class ExperimentList(BaseModel):
    experiments: List[ExperimentConfig]
