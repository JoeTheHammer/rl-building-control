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
