from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import SAC

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerProvider,
    load_rl_controller_config,
)
from environments.base_provider import IEnvironmentProvider


class SACController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)

        self.model = SAC("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        # Set log_interval to 1 to increase support for tensor flow integration (more regular logs).
        self.model.learn(timesteps, log_interval=1)


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

    def _build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> SACController:
        return SACController(env, hyper_params)

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> ControllerSetup:

        if config_path is None:
            raise RuntimeError("No configuration was provided for the SAC controller.")

        config = load_rl_controller_config(config_path)

        return super().create_rl_controller_setup(
            config=config,
            environment_provider=environment_provider,
            environment_config=environment_config,
            is_continuous_action_space=True,
            normalize_state=config.normalize_state,
        )
