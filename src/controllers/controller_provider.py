from abc import ABC, abstractmethod

import gym

from controllers.base_controller import IController
from experiment.experiment_config import ControllerConfig


class IControllerProvider(ABC):
    @abstractmethod
    def create_controller(self, env: gym.Env, config: ControllerConfig) -> IController:
        """
        Create and return a new controller instance.

        Args:
            env (gym.Env): The environment compatible with the controller.
            config (ControllerConfig): Algorithm-specific config.

        Returns:
            IController: A controller instance.
        """
        pass
