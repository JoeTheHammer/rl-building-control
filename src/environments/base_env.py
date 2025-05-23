from abc import ABC, abstractmethod
from typing import Any


class IEnvironment(ABC):
    """
    Interface for an experiment environment that can be interacted with by a controller or agent.
    Implementations must support environment reset and interaction through actions.
    """

    @abstractmethod
    def reset(self) -> Any:
        """
        Reset the environment to its initial state.

        Returns:
            Any: The initial state or observation after reset.
        """
        pass

    @abstractmethod
    def step(self, action: Any) -> Any:
        """
        Apply an action to the environment and progress one time step.

        Args:
            action (Any): The action to apply to the environment.

        Returns:
            Any: A tuple of (next_state, reward, done, info), where:
                - next_state: The resulting state after the action.
                - reward: The reward received from the transition.
                - done: Whether the episode has ended.
                - info: Additional diagnostic information.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Perform any necessary cleanup and release environment resources.

        This method should be called when the environment is no longer needed,
        to free up any system resources (e.g., processes, file handles, simulation engines).
        """
        pass
