from pydantic import BaseModel, Field

class KV(BaseModel):
    key: str
    value: str | float | int

class ControllerRule(BaseModel):
    condition: str
    action: str


class EnvironmentWrapper(BaseModel):
    normalizeState: bool = True
    normalizeReward: bool = True
    normalizeAction: bool = True
    continuousAction: bool = False
    discreteAction: bool = False


class ControllerSettings(BaseModel):
    type: str = "reinforcement learning"  # "reinforcement learning" | "rule based" | "custom"
    trainingTimesteps: int | None = None
    reportTraining: bool = False
    denormalize: bool = False
    tensorboardLogs: bool = False
    hpTuning: bool = False
    numEpisodes: int | None = None
    numTrials: int | None = None
    hyperparameters: list[KV] = Field(default_factory=list)
    environmentWrapper: EnvironmentWrapper = Field(default_factory=EnvironmentWrapper)
    customVariables: list[KV] = Field(default_factory=list)
    stateSpace: list[str] = Field(default_factory=list)
    rules: list[ControllerRule] = Field(default_factory=list)
    customModule: str = ""
    customClassName: str = ""
    initArguments: list[KV] = Field(default_factory=list)

class SaveControllerRequest(BaseModel):
    filename: str
    directory: str = "./data"
    settings: ControllerSettings
