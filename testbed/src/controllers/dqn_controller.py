from typing import Any, Dict

import gymnasium as gym
from gymnasium import Env
from stable_baselines3 import DQN

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


class DQNController(IRLController):
    """
    Controller for the Deep Q-Network (DQN) algorithm.
    This implementation uses the Stable-Baselines3 DQN, which includes
    improvements from Double DQN (DDQN) by default to prevent overestimation.
    """

    def __init__(self, env: gym.Env, params: Dict):
        """
        Initializes the DQN model with the given environment and parameters.
        DQN is a value-based, off-policy algorithm suitable for discrete action spaces.
        """
        super().__init__(env)
        self.model = DQN("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        """
        Predicts the deterministic action to take given the current state.
        For DQN, the action is chosen greedily with respect to the learned Q-values.
        """
        action, _ = self.model.predict(state, deterministic=True)
        return action

    def train(self, timesteps: int):
        """
        Trains the DQN model for a specified number of timesteps.
        """
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class DQNFactory(IRLControllerFactory):
    """
    Factory for the DQNController, including hyperparameter tuning with Optuna.
    This class suggests and builds a DQN controller with appropriate parameters.
    """

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DQNController:
        """
        Builds and returns a new DQNController instance.
        """
        return DQNController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        """
        Creates the DQN controller setup, loading configuration and environment.
        This method is the entry point for setting up the controller.
        """
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the DQN controller.")

        config = load_rl_controller_config(self.config_path)

        if config.hyperparameter_tuning.enabled:
            logger.warning("The DQN controller does not support hyperparameter tuning.")

        # This controlle relies on a discrete action space.
        config.environment_wrapper.discrete_action = True
        config.environment_wrapper.continuous_action = False

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        return super().create_rl_controller_setup(config.hyperparameters, env_wrap_manager)
