from abc import ABC, abstractmethod
from typing import Any, NamedTuple

import gymnasium as gym

from environments.base_factory import IEnvironmentFactory


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


class IControllerFactory(ABC):

    def __init__(self):
        self.config_path: str = ""
        self.env_factory: IEnvironmentFactory | None = None

    def set_config_path(self, config_path: str):
        self.config_path = config_path

    def set_env_factory(self, env_factory: IEnvironmentFactory):
        self.env_factory = env_factory

    @abstractmethod
    def create_controller_setup(self) -> ControllerSetup:
        """
        Create and return a new controller instance.

        Returns:
            IController: A controller instance.
        """
        pass
