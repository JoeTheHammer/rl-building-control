from typing import Dict, List, Optional, Union

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


class SinergymEnvironmentConfig(BaseModel):
    building_model: str
    weather_data: str
    state_space: StateSpace
    action_space: ActionSpace
