from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ReportingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    denormalize_state: bool = False


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    engine: str
    environment_config: str
    controller: str
    controller_config: Optional[str] = None
    reporting: ReportingConfig = None
    episodes: int = 1
    seed: Optional[int] = None


class ExperimentList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experiments: List[ExperimentConfig]
