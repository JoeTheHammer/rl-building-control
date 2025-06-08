from abc import ABC, abstractmethod

import gymnasium as gym

from controllers.base_controller import IController


class IControllerProvider(ABC):
    @abstractmethod
    def create_controller(self, env: gym.Env, config_path: str | None = None) -> IController:
        """
        Create and return a new controller instance.

        Args:
            env (gym.Env): The environment compatible with the controller.
            config_path (str | None): Optional path to the controller configuration file.

        Returns:
            IController: A controller instance.
        """
        pass
