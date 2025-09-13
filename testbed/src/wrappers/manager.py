import gymnasium as gym
from typing import List, Type, Optional

from gymnasium.wrappers import NormalizeObservation

from controllers.config import EnvironmentWrapper
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.discrete_action_wrapper import DiscreteActionWrapper


class EnvWrapperManager:
    """
    Manages a sequence of Gymnasium wrapper classes to be applied to an
    environment.
    """

    def __init__(
        self,
        wrapper_classes: Optional[List[Type[gym.Wrapper]]] = None,
        wrapper_config: EnvironmentWrapper = None,
    ):
        """
        Initializes the EnvWrapperManager.

        Args:
            wrapper_classes (Optional[List[Type[gym.Wrapper]]]): An optional
                                   initial list of wrapper classes.
        """
        self._wrapper_classes: List[Type[gym.Wrapper]] = (
            wrapper_classes if wrapper_classes is not None else []
        )
        if wrapper_config is not None:
            if wrapper_config.normalize_state:
                self.add_wrapper(NormalizeObservation)
            if wrapper_config.continuous_action:
                self.add_wrapper(ContinuousActionWrapper)
            if wrapper_config.discrete_action:
                self.add_wrapper(DiscreteActionWrapper)

    def add_wrapper(self, wrapper_class: Type[gym.Wrapper]):
        """
        Adds a wrapper class to the end of the list.

        Args:
            wrapper_class (Type[gym.Wrapper]): The wrapper class to add.
        """
        self._wrapper_classes.append(wrapper_class)

    def remove_wrapper(self, wrapper_class: Type[gym.Wrapper]):
        """
        Removes all occurrences of a specific wrapper class from the list.

        Args:
            wrapper_class (Type[gym.Wrapper]): The class of the wrapper to remove.
        """
        self._wrapper_classes = [cls for cls in self._wrapper_classes if cls is not wrapper_class]

    def apply_wrappers(self, env: gym.Env) -> gym.Env:
        """
        Applies the stored wrapper classes to an environment in order.

        Args:
            env (gym.Env): The base Gymnasium environment.

        Returns:
            gym.Env: The environment with all wrappers applied.
        """
        wrapped_env = env
        for wrapper_class in self._wrapper_classes:
            # Instantiate the wrapper class with the current environment
            wrapped_env = wrapper_class(wrapped_env)
        return wrapped_env
