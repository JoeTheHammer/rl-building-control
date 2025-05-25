from abc import abstractmethod
from typing import Any

import gymnasium as gym

from controllers.base_controller import IController


class RLController(IController):
    """
    Abstract base class for reinforcement learning controllers.

    This class extends the generic IController interface by assuming that
    the controller interacts with a gym-compatible environment and may rely
    on environment metadata (e.g., action_space, observation_space) for
    internal logic such as policy structure, sampling, or training.

    Subclasses must implement the get_action method.
    """

    def __init__(self, env: gym.Env):
        """
        Initialize the RLController with a reference to the environment.

        Args:
            env (gym.Env): The gym-compatible environment the controller interacts with.
        """
        self.env = env

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
