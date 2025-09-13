from typing import List, Optional

from pydantic import BaseModel


class ReportingConfig(BaseModel):
    denormalize_state: bool = False
    plots: bool = False
    export: bool = False


class ExperimentConfig(BaseModel):
    name: str
    engine: str
    environment_config: str
    controller: str
    controller_config: Optional[str] = None
    reporting: ReportingConfig = None
    episodes: int = 1


class ExperimentList(BaseModel):
    experiments: List[ExperimentConfig]
