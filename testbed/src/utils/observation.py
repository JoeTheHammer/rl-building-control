from typing import Any, Dict

import numpy as np


def build_info_dict(
    obs: np.ndarray,
    action: np.ndarray,
    time_info: Dict[str, Any],
    variables: Dict[str, tuple[str, str]],
    meters: Dict[str, str],
    actuators: Dict[str, tuple[str, str, str]],
) -> Dict[str, Any]:
    """
    Constructs a comprehensive observation dictionary containing:
    - Named state variables (from `variables`)
    - Meter readings (from `meters`)
    - Applied actuator values (from `actuators` and `action`)
    - Time info data (from `time_info`)

    The order of `obs` must match the order of keys in `variables` + `meters`.
    The order of `action` must match the order of keys in `actuators`.
    """
    ordered_state_keys = list(variables.keys()) + list(meters.keys())
    state_values = dict(zip(ordered_state_keys, obs))
    action_values = dict(zip(actuators.keys(), action))
    return {
        **state_values,
        **time_info,
        **action_values,
        "state_keys": ordered_state_keys + list(time_info.keys()),
        "action_keys": list(actuators.keys()),
    }
