from typing import Any

import numpy as np

from controllers.base_controller import IController


class MyCustomController(IController):
    """
    Example custom controller, that scales the action by a given factor while respecting given bounds
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.factor = kwargs.get("factor", 1.0)
        self.lower_bound = kwargs.get("lower_bound", 16.0)
        self.upper_bound = kwargs.get("upper_bound", 28.0)

    def get_action(self, state: Any) -> Any:
        sample = self.env.action_space.sample()

        clipped_action = tuple(
            np.clip(
                action_array * self.factor,  # Scale the individual NumPy array
                self.lower_bound,
                self.upper_bound,
            )
            for action_array in sample
        )
        return clipped_action
