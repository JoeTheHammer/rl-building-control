from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import TD3

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from environments.base_factory import IEnvironmentFactory


class TD3Controller(IRLController):
    """
    Controller for the Twin Delayed Deep Deterministic Policy Gradient (TD3) algorithm.
    """

    def __init__(self, env: gym.Env, params: Dict):
        """
        Initializes the TD3 model with the given environment and parameters.
        TD3 is a successor to DDPG that addresses its overestimation bias.
        """
        super().__init__(env)
        self.model = TD3("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        """
        Predicts the deterministic action to take given the current state.
        """
        # The predict method returns the deterministic action from the policy.
        action, _ = self.model.predict(state, deterministic=True)
        return action

    def train(self, timesteps: int):
        """
        Trains the TD3 model for a specified number of timesteps.
        """
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class TD3Factory(IRLControllerFactory):
    """
    Factory for the TD3Controller, including hyperparameter tuning with Optuna.
    This class suggests and builds a TD3 controller with appropriate parameters.
    """

    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:
        """
        Suggests hyperparameters for TD3, either returning defaults or using Optuna.
        TD3 includes specific parameters like policy_delay and target_policy_noise
        to stabilize learning.
        """
        if trial is None:
            # Return default values for TD3 if no Optuna trial is provided.
            # These values are based on the stable-baselines3 TD3 defaults.
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "buffer_size": 1000000,
                "tau": 0.005,
                "batch_size": 256,
                "policy_delay": 2,
                "target_policy_noise": 0.2,
                "target_noise_clip": 0.5,
            }

        # Suggest a search space for Optuna.
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "buffer_size": trial.suggest_int("buffer_size", 10000, 1000000, step=10000),
            "tau": trial.suggest_float("tau", 0.001, 0.05, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256]),
            "policy_delay": trial.suggest_int("policy_delay", 1, 5),
            "target_policy_noise": trial.suggest_float("target_policy_noise", 0.1, 0.5),
            "target_noise_clip": trial.suggest_float("target_noise_clip", 0.1, 0.5),
        }

    def _build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> TD3Controller:
        """
        Builds and returns a new TD3Controller instance.
        """
        return TD3Controller(env, hyper_params)

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_factory: IEnvironmentFactory | None = None,
    ) -> ControllerSetup:
        """
        Creates the TD3 controller setup, loading configuration and environment.
        This method is the entry point for setting up the controller.
        """
        if config_path is None:
            raise RuntimeError("No configuration was provided for the TD3 controller.")

        config = load_rl_controller_config(config_path)

        return super().create_rl_controller_setup(
            config=config,
            environment_factory=environment_factory,
            is_continuous_action_space=True,
            normalize_state=config.environment_wrapper.normalize_state,
        )
