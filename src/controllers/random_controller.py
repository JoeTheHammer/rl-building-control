from typing import Any

import gymnasium as gym

from controllers.base_controller import IController
from controllers.controller_provider import IControllerProvider
from experiment.experiment_config import ControllerConfig


class RandomController(IController):
    """
    A controller that randomly selects a valid action from the environment's action space.
    """

    def __init__(self, env: gym.Env):
        super().__init__(env)

    def get_action(self, state: Any) -> Any:
        """
        Sample a random action from the environment's action space.

        Args:
            state (Any): The current observation or state (ignored).

        Returns:
            Any: A randomly sampled action.
        """
        return self.env.action_space.sample()


class RandomControllerProvider(IControllerProvider):
    """
    Factory for creating instances of RandomController.

    This provider implements the IControllerProvider interface and can be registered
    in the experiment manager to instantiate RandomController objects when the configuration
    specifies a rule-based controller with logic type 'random'.
    """

    def create_controller(self, env: gym.Env, config: ControllerConfig) -> RandomController:
        """
        Create and return a new RandomController instance.

        Args:
            env (gym.Env): The gym-compatible environment to pass to the controller.
            config (ControllerConfig): The configuration block from the experiment definition.
                This implementation ignores the config, as RandomController requires only the environment.

        Returns:
            RandomController: A new controller instance using random actions.
        """
        return RandomController(env)
