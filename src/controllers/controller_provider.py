from abc import ABC, abstractmethod

import gymnasium as gym

from controllers.base_controller import IController
from environments.base_provider import IEnvironmentProvider


class IControllerProvider(ABC):
    @abstractmethod
    def create_controller(
        self,
        env: gym.Env,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> IController:
        """
        Create and return a new controller instance.

        Args:
            env (gym.Env): The environment compatible with the controller.
            config_path (str | None): Optional path to the controller configuration file.

        Returns:
            IController: A controller instance.
            :param env: Environment that is used.
            :param config_path: Path of configuration used to configure the controller.
            :param environment_config: Path to the configuration for the environment.
            :param environment_provider: Provider that allows to create new environment.
        """
        pass
