from typing import Tuple, Union

import gymnasium as gym
import numpy as np


class ContinuousActionWrapper(gym.ActionWrapper):
    """
    Wraps an environment with a complex action space (e.g., Tuple) and
    exposes a simple, continuous gym.spaces.Box to the agent.

    It requires the environment it wraps to have a custom attribute
    called '.discrete_mappings' that defines the real-world values for
    any Discrete subspaces.
    """

    def __init__(self, env: gym.Env):
        super().__init__(env)
        self._original_space = self.env.action_space

        if isinstance(self._original_space, gym.spaces.Tuple):
            self._is_tuple = True
            self._subspaces = self._original_space.spaces
        elif isinstance(self._original_space, gym.spaces.Box):
            self._is_tuple = False
            self._subspaces = [self._original_space]
        else:
            raise TypeError(
                f"Unsupported action space type: {type(self._original_space)}. "
                "This wrapper only supports Box and Tuple spaces."
            )

        if hasattr(env.unwrapped, "discrete_mappings"):
            self._mappings = env.unwrapped.discrete_mappings
        else:
            raise AttributeError(
                "The environment being wrapped by ContinuousActionMapper must have a "
                "'.discrete_mappings' attribute."
            )

        if len(self._subspaces) != len(self._mappings):
            raise ValueError(
                "The env's .discrete_mappings attribute has a different length "
                "than its number of action subspaces."
            )

        # Overwrite the public action_space to expose the new, unified Box space
        self.action_space = self._get_unified_box_space()

    def _get_unified_box_space(self) -> gym.spaces.Box:
        """
        Creates a single Box space representing the real-world actuator value bounds.
        """
        lows, highs = [], []
        for space, mapping in zip(self._subspaces, self._mappings):
            if isinstance(space, gym.spaces.Discrete):
                # Map discrete indices to actual actuator values
                if mapping is None or not mapping:
                    raise ValueError("A mapping must be provided for all Discrete subspaces.")
                lows.append(min(mapping))
                highs.append(max(mapping))
            elif isinstance(space, gym.spaces.Box):
                # Flatten multidimensional box bounds
                lows.extend(space.low.flatten().tolist())
                highs.extend(space.high.flatten().tolist())

        return gym.spaces.Box(
            low=np.array(lows, np.float32), high=np.array(highs, np.float32), dtype=np.float32
        )

    def action(self, action: np.ndarray) -> Union[np.ndarray, Tuple]:
        """
        Translates the agent's continuous action into the format expected by the
        original, underlying environment (e.g., a Tuple with discrete indices).
        """
        mapped_action_parts = []
        action_idx = 0
        for space, mapping in zip(self._subspaces, self._mappings):
            if isinstance(space, gym.spaces.Discrete):
                # Find the index of the closest valid real-world value
                agent_value = action[action_idx]
                allowed_values = np.array(mapping, dtype=np.float32)
                closest_index = np.abs(allowed_values - agent_value).argmin()
                mapped_action_parts.append(closest_index)
                action_idx += 1
            elif isinstance(space, gym.spaces.Box):
                # Take the corresponding slice of the action vector for the Box space
                dim = int(np.prod(space.shape))
                action_slice = action[action_idx : action_idx + dim].reshape(space.shape)
                mapped_action_parts.append(action_slice)
                action_idx += dim

        # Return the action in the format the original environment expects
        if self._is_tuple:
            return tuple(mapped_action_parts)
        else:
            return mapped_action_parts[0]
