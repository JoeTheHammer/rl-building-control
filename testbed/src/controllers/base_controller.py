from abc import ABC, abstractmethod
from typing import Any, NamedTuple

import gymnasium as gym

from environments.base_factory import EnvironmentFactory

from reporting.hdf5_storage import ExperimentStorage


class Controller(ABC):
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
    controller: Controller
    environment: gym.Env


class ControllerFactory(ABC):

    def __init__(self):
        self.config_path: str = ""
        self.env_factory: EnvironmentFactory | None = None
        self.experiment_storage: ExperimentStorage | None = None
        self.storage_flush_interval: int = 1024

    def set_config_path(self, config_path: str):
        self.config_path = config_path

    def set_env_factory(self, env_factory: EnvironmentFactory):
        self.env_factory = env_factory

    def set_experiment_storage(
        self,
        experiment_storage: ExperimentStorage | None,
        flush_interval: int = 1024,
    ) -> None:
        self.experiment_storage = experiment_storage
        self.storage_flush_interval = flush_interval

    @abstractmethod
    def create_controller_setup(self) -> ControllerSetup:
        """
        Create and return a new controller instance.

        Returns:
            Controller: A controller instance.
        """
        pass
