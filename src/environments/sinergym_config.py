from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel


class VariableConfig(BaseModel):
    type: str
    zone: str


class TimeFeatureConfig(BaseModel):
    cyclic: bool


class StateSpaceConfig(BaseModel):
    variables: Dict[str, VariableConfig]
    meters: Dict[str, str]
    time_info: Optional[Dict[str, TimeFeatureConfig]] = None


class ActuatorConfig(BaseModel):
    type: str
    component: str
    control_type: str
    actuator_key: str
    range: Optional[List[float]] = None
    values: Optional[List[float]] = None
    step_size: Optional[float] = None

class ActionSpaceConfig(BaseModel):
    actuators: Dict[str, ActuatorConfig]

class BaseRewardConfig(BaseModel):
    variables: Optional[List[str]] = None  # ← shared field


class ExpressionRewardConfig(BaseRewardConfig):
    type: Literal["expression"]
    expression: str
    params: Optional[Dict[str, Union[float, int, str]]] = None


class PythonRewardConfig(BaseRewardConfig):
    type: Literal["python"]
    module: str
    class_name: str
    init_args: Optional[Dict[str, Union[float, int, str]]] = None


RewardConfig = Union[ExpressionRewardConfig, PythonRewardConfig]


class EpisodeConfig(BaseModel):
    """Specifies optional episode parameters like simulation time."""

    timesteps_per_hour: Optional[int] = None
    period: Optional[List[int]] = None


class SinergymEnvironmentConfig(BaseModel):
    building_model: str
    weather_data: str
    state_space: StateSpaceConfig
    action_space: ActionSpaceConfig
    reward_function: RewardConfig
    normalize_state: Optional[bool] = False
    episode: Optional[EpisodeConfig] = None