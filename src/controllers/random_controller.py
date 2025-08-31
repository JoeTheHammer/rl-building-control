from typing import Any

import gymnasium as gym

from controllers.base_controller import ControllerSetup, IController, IControllerFactory
from environments.base_factory import IEnvironmentFactory


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


class RandomControllerFactory(IControllerFactory):
    """
    Factory for creating instances of RandomController.
    """

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_factory: IEnvironmentFactory | None = None,
    ) -> ControllerSetup:

        env = environment_factory.create_environment()

        controller = RandomController(env)

        return ControllerSetup(controller, env)
