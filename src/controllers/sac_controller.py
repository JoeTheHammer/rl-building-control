from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
import yaml
from gymnasium import Env
from pydantic import BaseModel
from stable_baselines3 import SAC

from controllers.base_rl_controller import IRLController, IRLControllerProvider
from environments.base_provider import IEnvironmentProvider


class HyperparameterTuning(BaseModel):
    num_trials: int
    num_episodes: int


class SACControllerConfig(BaseModel):
    train_timesteps: int
    hyperparameter_tuning: Optional[HyperparameterTuning] = None
    hyperparameters: Optional[Dict[str, Any]] = None


class SACController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)
        self.model = SAC(
            "MlpPolicy",
            self.env,
            learning_rate=params["learning_rate"],
            gamma=params["gamma"],
            ent_coef=params["ent_coef"],
            batch_size=params["batch_size"],
            verbose=0,
        )

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        self.model.learn(timesteps)


def load_controller_config(path: str) -> SACControllerConfig:
    """
    Loads a YAML controller configuration file and parses it into a SACControllerConfig object.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        SACControllerConfig: Parsed configuration object.
    """
    with open(path, "r") as f:
        raw_data = yaml.safe_load(f)
    return SACControllerConfig(**raw_data)


class SACProvider(IRLControllerProvider):

    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:

        if trial is None:
            # Return default values
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "ent_coef": "auto_1.0",
                "batch_size": 64,
            }

        # Use Optuna to suggest values
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "ent_coef": trial.suggest_float("ent_coef", 1e-8, 1e-1),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
        }

    def _build_controller(self, env: Env, hyper_params: Dict) -> SACController:
        return SACController(env, hyper_params)

    def create_controller(
        self,
        env: gym.Env,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> IRLController:
        config = load_controller_config(config_path)

        tuning = config.hyperparameter_tuning
        hyperparams = config.hyperparameters

        return super().create_rl_controller(
            env=env,
            environment_provider=environment_provider,
            environment_config=environment_config,
            train_timesteps=config.train_timesteps,
            is_continuous_action_space=True,
            num_trials=tuning.num_trials if tuning else None,
            num_episodes=tuning.num_episodes if tuning else None,
            hyperparameters=hyperparams,
        )
