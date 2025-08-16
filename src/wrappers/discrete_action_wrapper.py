import math

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Tuple


class DiscreteActionWrapper(gym.ActionWrapper):
    """
    A wrapper that converts a Tuple action space of an arbitrary number of Discrete spaces
    into a single Discrete action space.
    """

    def __init__(self, env):
        super().__init__(env)

        # Ensure the original action space is the expected type
        assert isinstance(env.action_space, Tuple), "Action space must be a Tuple"
        assert all(
            isinstance(space, Discrete) for space in env.action_space
        ), "Tuple must contain only Discrete spaces"

        # Calculate the size of the new combined discrete space
        self.discrete_sizes = [space.n for space in env.action_space]
        new_size = math.prod(self.discrete_sizes)
        self.action_space = Discrete(new_size)

    def action(self, action_index):
        """
        Maps a single discrete action index to the original action tuple.
        This method is called internally by the wrapper before passing the action
        to the wrapped environment.
        """
        actions = []
        temp_index = action_index
        # Iterate backwards to correctly compute the actions for each space
        for size in reversed(self.discrete_sizes):
            action = temp_index % size
            actions.insert(0, action)  # Prepend to maintain original order
            temp_index //= size
        return tuple(actions)

    def reverse_action(self, action_tuple):
        """
        Maps the original action tuple back to the single discrete action index.
        This can be useful for logging or debugging.
        """
        action_index = 0
        current_product = 1
        # Iterate backwards and compute the index
        for i in range(len(action_tuple) - 1, -1, -1):
            action_index += action_tuple[i] * current_product
            current_product *= self.discrete_sizes[i]
        return action_index

    def get_energy_plus_action(self, action_index: int) -> np.ndarray:
        """
        Gets the individual discrete actions (as a tuple of integers)
        and converts them to the corresponding real-valued actions.

        Note: This method is specifically designed for use in EnergyPlus environments
        that utilize a `custom_action_space` object with a `to_eplus_action` method. If this
        is not present, the passed action is returned.

        Args:
            action_index (int): The single integer action from the agent.

        Returns:
            np.ndarray: A flat NumPy array of real actuator values.
        """
        # First, map the agent's single action to the tuple of discrete actions
        discrete_actions_tuple = self.action(action_index)

        # Then, use the wrapped environment's method to convert the tuple
        # of discrete indices into real-valued actions.
        if hasattr(self.unwrapped, "custom_action_space"):
            return self.unwrapped.custom_action_space.to_eplus_action(discrete_actions_tuple)
        else:
            return discrete_actions_tuple
