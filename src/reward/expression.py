from typing import Any, Dict

import numpy as np
from asteval import Interpreter
from sinergym import BaseReward

from custom_loggers.experiment_logger import logger


def within(x, start, end):
    if start <= end:
        return start <= x <= end
    else:
        # Allow wrap-around for cases like Nov (11) to Mar (3)
        return x >= start or x <= end


class ExpressionReward(BaseReward):
    def __init__(self, expression: str, params: dict = None):
        super().__init__()
        self.expression = expression
        self.params = params
        self.aeval = Interpreter(
            usersyms={
                "abs": abs,
                "min": min,
                "max": max,
                "exp": np.exp,
                "clip": np.clip,
                "sqrt": np.sqrt,
                "within": within,
            },
            no_print=True,
        )

    def __call__(self, obs_dict) -> (float, Dict[str, Any]):
        # Combine the observations with parameters
        local_dict = {**obs_dict, **self.params}

        self.aeval.symtable.clear()
        self.aeval.symtable.update(local_dict)

        try:
            reward = float(self.aeval(self.expression))
        except Exception as e:
            reward = -999.99
            logger.error(f"[ExpressionReward] Evaluation error {e}")

        return reward, {"reward": reward}
