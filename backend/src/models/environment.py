from pydantic import BaseModel, Field

# ----- General -----
class EnvironmentGeneralSettings(BaseModel):
    buildingModelFile: str | None = None
    weatherDataFile: str | None = None
    startDate: str = ""
    endDate: str = ""
    timestepsPerHour: int | None = None

# ----- State space -----
class TimeFlag(BaseModel):
    included: bool = False
    cyclic: bool = False

class EnvVariable(BaseModel):
    name: str
    variableType: str  # "variable" or "meter"
    energyPlusType: str | None = None
    zone: str | None = None
    meterName: str | None = None
    excludeFromState: bool = False

class EnvStateSpaceSettings(BaseModel):
    addTimeInfo: bool = False
    dayOfMonth: TimeFlag
    month: TimeFlag
    dayOfWeek: TimeFlag
    hour: TimeFlag
    minute: TimeFlag
    variables: list[EnvVariable] = Field(default_factory=list)

# ----- Action space -----
class Actuator(BaseModel):
    actuatorName: str
    component: str
    controlType: str
    actuatorKey: str
    type: str  # "continuous" or "discrete"
    mode: str | None = None
    valueList: list[float] = Field(default_factory=list)
    min: float | None = None
    max: float | None = None
    stepSize: float | None = None

class EnvActionSpaceSettings(BaseModel):
    actuators: list[Actuator] = Field(default_factory=list)

# ----- Reward -----
class RewardParameterKV(BaseModel):
    key: str
    value: float

class EnvironmentRewardSettings(BaseModel):
    type: str = "expression"
    variables: list[str] = Field(default_factory=list)
    expression: str = ""
    parameters: list[RewardParameterKV] = Field(default_factory=list)

# ----- Full config -----
class EnvironmentConfig(BaseModel):
    generalSettings: EnvironmentGeneralSettings
    stateSpaceSettings: EnvStateSpaceSettings
    actionSpaceSettings: EnvActionSpaceSettings
    rewardSettings: EnvironmentRewardSettings

class SaveEnvironmentRequest(BaseModel):
    filename: str
    directory: str = "./data"
    config: EnvironmentConfig
