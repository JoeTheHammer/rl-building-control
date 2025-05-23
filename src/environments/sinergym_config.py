from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel


class Variable(BaseModel):
    type: str
    zone: str


class StateSpace(BaseModel):
    variables: Dict[str, Variable]
    meters: Dict[str, str]


class Actuator(BaseModel):
    type: str
    component: str
    control_type: str
    actuator_key: str
    range: Optional[List[float]] = None
    values: Optional[List[Union[str, int]]] = None


class ActionSpace(BaseModel):
    actuators: Dict[str, Actuator]

class ExpressionRewardConfig(BaseModel):
    type: Literal["expression"]
    expression: str
    params: Optional[Dict[str, Union[float, int, str]]] = None


class PythonRewardConfig(BaseModel):
    type: Literal["python"]
    module: str  # e.g., "my_rewards.custom"
    class_name: str  # e.g., "MyCustomReward"
    init_args: Optional[Dict[str, Union[float, int, str]]] = None


RewardConfig = Union[ExpressionRewardConfig, PythonRewardConfig]


class SinergymEnvironmentConfig(BaseModel):
    building_model: str
    weather_data: str
    state_space: StateSpace
    action_space: ActionSpace
    reward_function: RewardConfig