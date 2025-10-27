from typing import Optional, Any, Dict

from pydantic import BaseModel, Field


class Training(BaseModel):
    timesteps: int
    report_training: Optional[bool] = False
    report_denormalized_state: Optional[bool] = False
    tensorboard_logs: Optional[bool] = False


class HyperparameterTuning(BaseModel):
    enabled: bool = False
    num_trials: int
    num_episodes: int
    sampler: str = None


class EnvironmentWrapper(BaseModel):
    normalize_state: Optional[bool] = True
    normalize_reward: Optional[bool] = True
    normalize_action: Optional[bool] = True
    continuous_action: Optional[bool] = False
    discrete_action: Optional[bool] = False


class RLControllerConfig(BaseModel):
    training: Training
    hyperparameter_tuning: Optional[HyperparameterTuning] = None
    environment_wrapper: EnvironmentWrapper = Field(default_factory=EnvironmentWrapper)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
