from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VariableConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(validation_alias="type")
    zone: str
    exclude_from_state: bool = False


class MeterConfig(BaseModel):
    name: str
    exclude_from_state: bool = False


class TimeFeatureConfig(BaseModel):
    cyclic: bool


class StateSpaceConfig(BaseModel):
    variables: Dict[str, VariableConfig]
    meters: Dict[str, MeterConfig] = Field(default_factory=dict)
    time_info: Optional[Dict[str, TimeFeatureConfig]] = None

    @field_validator("meters", mode="before")
    @classmethod
    def _normalize_meters(cls, value: Optional[Dict[str, object]]):
        if value is None:
            return {}

        normalized: Dict[str, object] = {}
        for key, meter in value.items():
            if isinstance(meter, str):
                normalized[key] = {"name": meter}
            else:
                normalized[key] = meter
        return normalized


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
    variables: Optional[List[str]] = None  # shared field


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


WeatherVariabilityTuple = tuple[float, float, float]


class SinergymEnvironmentConfig(BaseModel):
    building_model: str
    weather_data: str

    weather_variability: Optional[Dict[str, WeatherVariabilityTuple]] = None

    state_space: StateSpaceConfig
    action_space: ActionSpaceConfig
    reward_function: RewardConfig
    episode: Optional[EpisodeConfig] = None

    @field_validator("weather_variability", mode="before")
    @classmethod
    def _normalize_weather_variability(cls, v):
        """
        Accepts mapping: variable_name -> [sigma, mu, tau]
        and stores it as: variable_name -> (sigma, mu, tau)
        """
        if v is None:
            return None
        if not isinstance(v, dict):
            raise TypeError(
                "weather_variability must be a mapping: variable_name -> [sigma, mu, tau]"
            )

        out: Dict[str, WeatherVariabilityTuple] = {}
        for key, item in v.items():
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                raise ValueError(
                    f"weather_variability['{key}'] must be a list/tuple of exactly 3 numbers: [sigma, mu, tau]"
                )
            sigma, mu, tau = item
            out[key] = (float(sigma), float(mu), float(tau))
        return out
