from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import DDPG

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from environments.base_factory import IEnvironmentFactory
from wrappers.manager import EnvWrapperManager
from gymnasium.wrappers import NormalizeObservation
from wrappers.continuous_action_wrapper import ContinuousActionWrapper


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


class DDPGFactory(IRLControllerFactory):
    """
    Factory for the DDPGController
    """

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DDPGController:
        """
        Builds and returns a new DDPGController instance.
        """
        return DDPGController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        """
        Creates the DDPG controller setup, loading configuration and environment.
        """
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the DDPG controller.")

        config = load_rl_controller_config(self.config_path)

        env_wrap_manager = EnvWrapperManager([NormalizeObservation, ContinuousActionWrapper],
                                             config.environment_wrapper)

        return super().create_rl_controller_setup_new(config.hyperparameters, env_wrap_manager)
