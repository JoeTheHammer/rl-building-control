from typing import Any, Dict

import gymnasium as gym
from gymnasium import Env
from stable_baselines3 import TD3

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


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

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> TD3Controller:
        """
        Builds and returns a new TD3Controller instance.
        """
        return TD3Controller(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        """
        Creates the TD3 controller setup, loading configuration and environment.
        This method is the entry point for setting up the controller.
        """
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the TD3 controller.")

        config = load_rl_controller_config(self.config_path)

        if config.hyperparameter_tuning.enabled:
            logger.warning("The TD3 controller does not support hyperparameter tuning.")

        # This controller relies on a continuous action space.
        config.environment_wrapper.discrete_action = False
        config.environment_wrapper.continuous_action = True

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        return super().create_rl_controller_setup(config.hyperparameters, env_wrap_manager)
