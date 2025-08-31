from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import DDPG

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerProvider,
    load_rl_controller_config,
)
from environments.base_factory import IEnvironmentFactory


class DDPGController(IRLController):
    """
    Controller for the Deep Deterministic Policy Gradient (DDPG) algorithm.
    """

    def __init__(self, env: gym.Env, params: Dict):
        """
        Initializes the DDPG model with the given environment and parameters.
        """
        super().__init__(env)
        self.model = DDPG("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        """
        Predicts the action to take given the current state.
        """
        # The predict method returns the deterministic action from the policy.
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        """
        Trains the DDPG model for a specified number of timesteps.
        """
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class DDPGProvider(IRLControllerProvider):
    """
    Provider for the DDPGController, including hyperparameter tuning with Optuna.
    """

    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:
        """
        Suggests hyperparameters for DDPG, either returning defaults or using Optuna.
        """
        if trial is None:
            # Return default values for DDPG if no Optuna trial is provided.
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "buffer_size": 100000,
                "tau": 0.005,
                "batch_size": 64,
            }

        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "buffer_size": trial.suggest_int("buffer_size", 10000, 1000000, step=10000),
            "tau": trial.suggest_float("tau", 0.001, 0.05, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256]),
        }

    def _build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DDPGController:
        """
        Builds and returns a new DDPGController instance.
        """
        return DDPGController(env, hyper_params)

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_provider: IEnvironmentFactory | None = None,
        environment_config: str | None = None,
    ) -> ControllerSetup:
        """
        Creates the DDPG controller setup, loading configuration and environment.
        """
        if config_path is None:
            raise RuntimeError("No configuration was provided for the DDPG controller.")

        config = load_rl_controller_config(config_path)

        return super().create_rl_controller_setup(
            config=config,
            environment_provider=environment_provider,
            environment_config=environment_config,
            is_continuous_action_space=True,
            normalize_state=config.normalize_state,
        )

