import gymnasium as gym
from typing import List, Type, Optional

class EnvWrapperManager:
    """
    Manages a sequence of Gymnasium wrappers to be applied to an environment.
    """
    def __init__(self, wrappers: Optional[List[gym.Wrapper]] = None):
        """
        Initializes the EnvWrapperManager.

        Args:
            wrappers (Optional[List[gym.Wrapper]]): An optional initial list of
                                                    wrapper instances.
        """
        self._wrappers: List[gym.Wrapper] = wrappers if wrappers is not None else []

    def add_wrapper(self, wrapper: gym.Wrapper):
        """
        Adds a wrapper to the end of the list.

        Args:
            wrapper (gym.Wrapper): The wrapper instance to add.
        """
        self._wrappers.append(wrapper)

    def remove_wrapper(self, wrapper_class: Type[gym.Wrapper]):
        """
        Removes all occurrences of a specific wrapper class from the list.

        Args:
            wrapper_class (Type[gym.Wrapper]): The class of the wrapper to remove.
        """
        self._wrappers = [
            wrapper for wrapper in self._wrappers
            if not isinstance(wrapper, wrapper_class)
        ]

    def apply_wrappers(self, env: gym.Env) -> gym.Env:
        """
        Applies the stored wrappers to an environment in order.

        Args:
            env (gym.Env): The base Gymnasium environment.

        Returns:
            gym.Env: The environment with all wrappers applied.
        """
        wrapped_env = env
        for wrapper in self._wrappers:
            # Re-initialize the wrapper with the current environment
            wrapped_env = type(wrapper)(wrapped_env)
        return wrapped_env