from typing import List, Optional, Union

import gymnasium as gym
import numpy as np


class ActuatorActionSpace:
    """
    A custom action space wrapper that combines discrete and continuous (Box) action spaces.
    It provides a unified interface for translating agent actions into real-valued actuator commands,
    suitable for use in building control or other mixed-control environments.

    Attributes:
        spaces (List[Union[Box, Discrete]]): A list of action spaces (either Box or Discrete).
        discrete_mappings (List[Optional[List[float]]]): Maps for Discrete spaces, where each index maps to a real-valued actuator setting.
        tuple_space (gymnasium.spaces.Tuple): Internal tuple space combining all subspaces.
    """

    def __init__(
        self,
        spaces: List[Union[gym.spaces.Box, gym.spaces.Discrete]],
        discrete_mappings: List[Optional[List[float]]],
    ):
        """
        Initialize the mixed action space wrapper.

        Args:
            spaces (List[Union[Box, Discrete]]): The individual action spaces for each actuator.
            discrete_mappings (List[Optional[List[float]]]): The real-world value mapping for each discrete space.
                Use None for Box spaces.
        """

        self.tuple_space = gym.spaces.Tuple(spaces)
        self.discrete_mappings = discrete_mappings
        self.spaces = spaces

    def to_eplus_action(self, action_tuple: np.ndarray) -> np.ndarray:
        """
        Convert a tuple-style action from the agent into a flat NumPy array
        of real values suitable for EnergyPlus.

        Args:
            action_tuple (np.ndarray): Action values from the agent (discrete indices or continuous values).

        Returns:
            np.ndarray: Flat array of real actuator values.
        """
        flat_action = []
        for val, space, mapping in zip(action_tuple, self.spaces, self.discrete_mappings):
            if isinstance(space, gym.spaces.Discrete):
                flat_action.append(mapping[val])
            elif isinstance(space, gym.spaces.Box):
                flat_action.append(float(val[0]))
            else:
                raise ValueError(f"Unsupported space type: {type(space)}")
        return np.array(flat_action, dtype=np.float32)

    def map_continuous_to_valid_actions(self, action_vec: np.ndarray) -> np.ndarray:
        """
        Maps a continuous action vector (as output by a continuous controller) to valid actuator values.
        For discrete actuators, this means picking the closest allowed value.
        For continuous actuators, the value is passed through.
        """
        mapped_action = []
        for val, space, mapping in zip(action_vec, self.spaces, self.discrete_mappings):
            if isinstance(space, gym.spaces.Discrete):
                allowed = np.array(mapping, dtype=np.float32)
                float_val = (
                    float(val)
                    if np.isscalar(val) or isinstance(val, (np.floating, float))
                    else float(val[0])
                )
                idx = np.abs(allowed - float_val).argmin()
                mapped_action.append(allowed[idx])
            elif isinstance(space, gym.spaces.Box):
                mapped_action.append(
                    float(val[0]) if isinstance(val, (np.ndarray, list)) else float(val)
                )
            else:
                raise ValueError(f"Unsupported space type: {type(space)}")
        return np.array(mapped_action, dtype=np.float32)

    def get_box_space(self) -> gym.spaces.Box:
        """
        Get a unified continuous Box space that reflects the actual actuator value bounds
        for all actions, including those originally defined as Discrete.

        Returns:
            gymnasium.spaces.Box: A Box space with shape (n,), where n is the number of actuators.
        """

        lows, highs = [], []

        for space, mapping in zip(self.spaces, self.discrete_mappings):
            if isinstance(space, gym.spaces.Discrete):
                # Map discrete indices to actual actuator values
                if mapping is None or not mapping:
                    raise ValueError("Discrete space must have a value mapping.")
                lows.append(min(mapping))
                highs.append(max(mapping))

            elif isinstance(space, gym.spaces.Box):
                # Flatten multidimensional box bounds
                lows.extend(space.low.flatten().tolist())
                highs.extend(space.high.flatten().tolist())

            else:
                raise NotImplementedError(f"Unsupported space type: {type(space)}")

        return gym.spaces.Box(
            low=np.array(lows, dtype=np.float32),
            high=np.array(highs, dtype=np.float32),
            dtype=np.float32,
        )
