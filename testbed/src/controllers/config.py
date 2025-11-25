from typing import Optional, Any, Dict

from pydantic import BaseModel, Field, field_validator


class Training(BaseModel):
    timesteps: int
    report_training: Optional[bool] = False
    report_denormalized_state: Optional[bool] = False
    tensorboard_logs: Optional[bool] = False


class HyperparameterTuning(BaseModel):
    enabled: bool = False
    num_trials: int
    num_episodes: int
    training_timesteps: int
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

    @field_validator("hyperparameters", mode="before")
    def parse_dot_notation(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses keys with dots into nested dictionaries.
        """

        new_hyperparams = {}

        for k, v in value.items():
            if "." in k:
                keys = k.split(".")
                current_level = new_hyperparams

                for sub_key in keys[:-1]:
                    if sub_key not in current_level:
                        current_level[sub_key] = {}
                    current_level = current_level[sub_key]

                    if not isinstance(current_level, dict):
                        raise ValueError(
                            f"Conflict at key '{sub_key}'. It is already defined as a non-dict value."
                        )

                current_level[keys[-1]] = v
            else:
                new_hyperparams[k] = v

        return new_hyperparams
