from typing import Any, Dict

import gymnasium as gym
from gymnasium import Env
from stable_baselines3 import SAC

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from gymnasium.wrappers import NormalizeObservation
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager


class SACController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)

        self.model = SAC("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        # Set log_interval to 1 to increase support for tensor graph integration (more regular logs).
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class SACFactory(IRLControllerFactory):

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> SACController:
        return SACController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the SAC controller.")

        config = load_rl_controller_config(self.config_path)

        env_wrap_manager = EnvWrapperManager(
            [ContinuousActionWrapper], config.environment_wrapper
        )

        return super().create_rl_controller_setup(config.hyperparameters, env_wrap_manager)
