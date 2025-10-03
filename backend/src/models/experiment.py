from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExperimentReporting(BaseModel):
    plots: bool = False
    denormalizeState: bool = False
    export: bool = False


class ExperimentConfig(BaseModel):
    name: str = ""
    engine: str = ""
    environmentConfig: str = ""
    controller: str = ""
    controllerConfig: str = ""
    episodes: int | None = None
    reporting: ExperimentReporting = Field(default_factory=ExperimentReporting)


class SaveExperimentRequest(BaseModel):
    filename: str
    directory: str = "./data"
    experiments: list[ExperimentConfig] = Field(default_factory=list)


class ExperimentSuiteStatus(str, Enum):
    NEW = "New"
    RUNNING = "Running"
    FINISHED = "Finished"
    ABORTED = "Aborted"


class RunExperimentSuiteRequest(BaseModel):
    config_name: str
    suite_name: str


class TensorBoardStatus(BaseModel):
    enabled: bool = False
    running: bool = False
    url: Optional[str] = None
    port: Optional[int] = None
    pid: Optional[int] = None
    owner: Optional[str] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ExperimentSuiteResponse(BaseModel):
    id: int
    name: str
    status: ExperimentSuiteStatus
    pid: int | None = None
    path: str | None = None
    config_filename: str | None = None
    archived: bool = False
    tensorboard_enabled: bool = False
    tensorboard: TensorBoardStatus = Field(default_factory=TensorBoardStatus)


class StopExperimentSuiteResponse(BaseModel):
    id: int
    status: ExperimentSuiteStatus


class ExperimentConfigSection(BaseModel):
    filename: str
    content: Dict[str, Any] = Field(default_factory=dict)


class ExperimentConfigDetailsExperiment(BaseModel):
    id: int
    name: Optional[str] = None
    environment: Optional[ExperimentConfigSection] = None
    controller: Optional[ExperimentConfigSection] = None
    environment_path: Optional[str] = None
    controller_path: Optional[str] = None


class ExperimentConfigDetailsResponse(BaseModel):
    experiment: ExperimentConfigSection
    environment: Optional[ExperimentConfigSection] = None
    controller: Optional[ExperimentConfigSection] = None
    experiments: List[ExperimentConfigDetailsExperiment] = Field(default_factory=list)


class ExperimentProgress(BaseModel):
    id: int
    name: Optional[str] = None
    status: Optional[str] = None
    total_training_episodes: Optional[int] = None
    current_training_episode: Optional[int] = None
    total_evaluation_episodes: Optional[int] = None
    current_evaluation_episode: Optional[int] = None


class ExperimentRunStatus(BaseModel):
    experiments: List[ExperimentProgress] = Field(default_factory=list)


class ExperimentLogResponse(BaseModel):
    content: str = ""


class TensorBoardStatusResponse(TensorBoardStatus):
    suite_id: int


class StopTensorBoardResponse(TensorBoardStatusResponse):
    stopped: bool = False


class StartTensorBoardRequest(BaseModel):
    owner: Optional[str] = None


class StopTensorBoardRequest(BaseModel):
    reason: Optional[str] = None
