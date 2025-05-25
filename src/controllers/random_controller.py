from typing import Any

import gymnasium as gym

from controllers.rl_controller import RLController


class RandomController(RLController):
    """
    A controller that randomly selects a valid action from the environment's action space.
    """

    def __init__(self, env: gym.Env):
        super().__init__(env)

    def get_action(self, state: Any) -> Any:
        """
        Sample a random action from the environment's action space.

        Args:
            state (Any): The current observation or state (ignored).

        Returns:
            Any: A randomly sampled action.
        """
        return self.env.action_space.sample()
