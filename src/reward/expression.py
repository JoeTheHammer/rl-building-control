from math import exp
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


def _to_scalar(v):
    if isinstance(v, np.ndarray) and v.size == 1:
        return float(v[0])
    if isinstance(v, (np.floating, np.integer)):
        return float(v)
    return v


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
                "exp": exp,
                "clip": np.clip,
                "sqrt": np.sqrt,
                "within": within,
            },
            no_print=True,
        )

    def __call__(self, obs_dict) -> (float, Dict[str, Any]):
        # Merge and convert all values to native types
        combined = {**obs_dict, **self.params}
        local_dict = {k: _to_scalar(v) for k, v in combined.items()}

        self.aeval.symtable.update(local_dict)

        try:
            result = self.aeval(self.expression)
        except Exception as e:
            result = 0  # No signal at all if reward cannot be determined.
            if self.aeval.error:
                logger.error(f"[ExpressionReward] Evaluation error {self.aeval.error}")
            else:
                logger.error(f"[ExpressionReward] Evaluation error {e}")

        reward = float(result)

        return reward, {"reward": reward}
