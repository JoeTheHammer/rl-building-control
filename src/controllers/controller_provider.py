from abc import ABC, abstractmethod

import gym

from controllers.base_controller import IController


class IControllerProvider(ABC):
    @abstractmethod
    def create_controller(self, env: gym.Env, config_path: str) -> IController:
        """
        Create and return a new controller instance.

        Args:
            env (gym.Env): The environment compatible with the controller.
            config_path (str): Path to the config file.

        Returns:
            IController: A controller instance.
        """
        pass
