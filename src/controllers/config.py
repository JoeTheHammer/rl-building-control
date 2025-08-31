from typing import Optional, Any, Dict

from pydantic import BaseModel


class Training(BaseModel):
    timesteps: int
    report_training: Optional[bool] = False
    report_denormalized_state: Optional[bool] = False


class HyperparameterTuning(BaseModel):
    enabled: Optional[bool] = False
    num_trials: int
    num_episodes: int


class EnvironmentWrapper(BaseModel):
    normalize_state: Optional[bool] = True
    continuous_action: Optional[bool] = False
    discrete_action: Optional[bool] = False


class RLControllerConfig(BaseModel):
    training: Training
    hyperparameter_tuning: Optional[HyperparameterTuning]
    environment_wrapper: Optional[EnvironmentWrapper] = EnvironmentWrapper()
    hyperparameters: Optional[Dict[str, Any]] = None
