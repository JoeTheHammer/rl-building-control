from abc import ABC, abstractmethod
from typing import Any


class IController(ABC):
    """
    Abstract base class for controllers that produce actions based on the environment.
    """

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
