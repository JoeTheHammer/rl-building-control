import math

import gymnasium as gym
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
        assert all(isinstance(space, Discrete) for space in
                   env.action_space), "Tuple must contain only Discrete spaces"

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