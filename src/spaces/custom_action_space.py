from typing import List, Optional, Union

import gymnasium
import numpy as np
from gymnasium.spaces import Box, Discrete


class CustomActionSpace:
    def __init__(
        self, spaces: List[Union[Box, Discrete]], discrete_mappings: List[Optional[List[float]]]
    ):
        self.tuple_space = gymnasium.spaces.Tuple(spaces)
        self.discrete_mappings = discrete_mappings
        self.spaces = spaces

    def to_eplus_action(self, action_tuple: np.ndarray) -> np.ndarray:
        """Convert tuple action to a flat ndarray of real values."""
        flat_action = []
        for val, space, mapping in zip(action_tuple, self.spaces, self.discrete_mappings):
            if isinstance(space, Discrete):
                flat_action.append(mapping[val])
            elif isinstance(space, Box):
                flat_action.append(float(val[0]))
            else:
                raise ValueError(f"Unsupported space type: {type(space)}")
        return np.array(flat_action, dtype=np.float32)

    def get_box_space(self) -> Box:
        """
        Return a Box space that represents the actual value bounds
        for each actuator, whether discrete or continuous.
        Each actuator maps to one dimension.

        Returns:
            gym.spaces.Box: A Box of shape (n,), where n is the number of actuators.
        """
        lows, highs = [], []

        for space, mapping in zip(self.spaces, self.discrete_mappings):
            if isinstance(space, Discrete):
                # Map discrete indices to actual actuator values
                if mapping is None or not mapping:
                    raise ValueError("Discrete space must have a value mapping.")
                lows.append(min(mapping))
                highs.append(max(mapping))

            elif isinstance(space, Box):
                # Assumes scalar Boxes only — if shape > 1, raise error or flatten
                if space.shape != (1,):
                    raise ValueError("Multi-dimensional Box not supported in flat box export.")
                lows.append(space.low[0])
                highs.append(space.high[0])

            else:
                raise NotImplementedError(f"Unsupported space type: {type(space)}")

        return Box(
            low=np.array(lows, dtype=np.float32),
            high=np.array(highs, dtype=np.float32),
            dtype=np.float32,
        )
