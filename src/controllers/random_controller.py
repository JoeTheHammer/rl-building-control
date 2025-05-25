from typing import Any

import gym
import numpy as np
from gymnasium import Space

from controllers.base_controller import IController


class RandomController(IController):
    """
    A controller that randomly selects valid actions for each actuator
    based on the provided ActionSpace definition.
    """
    
    def __init__(self, env: gym.Env):
        super().__init__(env)

    def get_action(self, state: Any) -> Any:
        """
        Generate a random valid action for each actuator.

        Args:
            state (Any): The current state or observation (ignored).

        Returns:
            np.ndarray: Action vector with one value per actuator, ordered by the ActionSpace.
        """
        action_space: Space = self.env.action_space
        if not action_space:
            raise ValueError("Missing required 'action_space' argument")

        action_values = []

        # TODO: Get Information from the space and create reward function

        return np.array(action_values, dtype=np.float32)
