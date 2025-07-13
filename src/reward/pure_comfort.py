# This is a placeholder for your actual logger
import logging
from typing import Any, Dict

import numpy as np
from sinergym import BaseReward

logger = logging.getLogger(__name__)


def _to_scalar(v):
    """Converts numpy arrays of size 1 and numpy numbers to Python floats."""
    if isinstance(v, np.ndarray) and v.size == 1:
        return float(v[0])
    if isinstance(v, (np.floating, np.integer)):
        return float(v)
    return v


class PureComfortReward(BaseReward):
    """
    An ultra-simplified reward function focused exclusively on comfort.

    The reward is the negative sum of the absolute differences between the
    current air temperatures and the desired target temperature. The agent's
    sole objective is to make this reward as close to zero as possible by
    maintaining both rooms at the target temperature.
    """

    def __init__(self):
        super().__init__()
        self.target_temp = 23.0

    def __call__(self, reward_dict) -> (float, Dict[str, Any]):
        local_dict = {k: _to_scalar(v) for k, v in reward_dict.items()}

        # Get current air temperatures
        air_temp_1 = local_dict.get("air_temp_101")
        air_temp_2 = local_dict.get("air_temp_104")

        # --- The entire reward calculation ---
        # The reward is the negative total deviation from the target.
        # The goal is to drive this value to 0.
        reward = 0
        if air_temp_1 is not None:
            reward -= abs(air_temp_1 - self.target_temp)
        if air_temp_2 is not None:
            reward -= abs(air_temp_2 - self.target_temp)

        return reward, {"reward": reward}
