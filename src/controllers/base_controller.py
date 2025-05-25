from abc import ABC, abstractmethod
from typing import Any

import gymnasium as gym


class IController(ABC):
    """
    Abstract base class for controllers that produce actions based on the environment.
    """

    def __init__(self, env: gym.Env):
        """
        Initialize the controller with the environment it will interact with.

        Args:
            env (gym.Env): The environment with which the controller will interact.
        """
        self.env = env

    @abstractmethod
    def get_action(self, state: Any) -> Any:
        """
        Compute and return an action given the current state.

        Args:
            state (Any): The current environment state or observation.

        Returns:
            Any: The computed action.
        """
        pass
