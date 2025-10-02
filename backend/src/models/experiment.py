from enum import Enum

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


class ExperimentSuiteResponse(BaseModel):
    id: int
    name: str
    status: ExperimentSuiteStatus
    pid: int | None = None
    path: str | None = None
    config_filename: str | None = None


class StopExperimentSuiteResponse(BaseModel):
    id: int
    status: ExperimentSuiteStatus
