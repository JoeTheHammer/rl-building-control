from abc import ABC, abstractmethod
from typing import Any, NamedTuple

import gymnasium as gym

from environments.base_provider import IEnvironmentProvider


class IController(ABC):
    """
    Abstract base class for controllers that produce actions based on the environment.
    """

    def __init__(self, env: gym.Env, **kwargs: Any):
        """
        Initialize the Controller with a reference to the environment and
        optionally additional parameters required by specific algorithms.

        Args:
            env (gym.Env): The gym-compatible environment the controller interacts with.
            **kwargs (Any): Optional keyword arguments for RL-specific needs (e.g., model paths, policies).
        """
        self.env = env
        self.extra_args = kwargs

    @abstractmethod
    def get_action(self, state: Any) -> Any:
        """
        Compute and return the action based on the current state.

        This method must be implemented by subclasses and can rely on internal models,
        learned policies, or other RL mechanisms.

        Args:
            state (Any): The current observation or state from the environment.

        Returns:
            Any: The action to apply, typically matching the environment's action space.
        """
        pass



class ControllerSetup(NamedTuple):
    controller: IController
    environment: gym.Env

class IControllerProvider(ABC):
    @abstractmethod
    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> ControllerSetup:
        """
        Create and return a new controller instance.

        Args:
            env (gym.Env): The environment compatible with the controller.
            config_path (str | None): Optional path to the controller configuration file.
            environment_provider (IEnvironmentProvider | None): Optional Environment provider to create environments for training and tuning.
            environment_config (str | None): Optional path to the controller configuration file.

        Returns:
            IController: A controller instance.
            :param config_path: Path of configuration used to configure the controller.
            :param environment_config: Path to the configuration for the environment.
            :param environment_provider: Provider that allows to create new environment.
        """
        pass

