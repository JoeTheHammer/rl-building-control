from typing import Any, Dict, List

import numpy as np


def build_observation_dict(
    obs: np.ndarray,
    action: np.ndarray,
    info: Dict[str, Any],
    variables: Dict[str, tuple[str, str]],
    meters: Dict[str, str],
    actuators: Dict[str, tuple[str, str, str]],
) -> Dict[str, Any]:
    """
    Constructs a comprehensive observation dictionary containing:
    - Named state variables (from `variables`)
    - Meter readings (from `meters`)
    - Applied actuator values (from `actuators` and `action`)
    - Episode metadata (from `info`)

    The order of `obs` must match the order of keys in `variables` + `meters`.
    The order of `action` must match the order of keys in `actuators`.
    """
    ordered_state_keys = list(variables.keys()) + list(meters.keys())
    state_values = dict(zip(ordered_state_keys, obs))
    action_values = dict(zip(actuators.keys(), action))
    return {**state_values, **action_values, **info}
