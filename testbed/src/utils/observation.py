from typing import Any, Dict

import numpy as np


def build_info_dict(
    obs: np.ndarray,
    action: np.ndarray,
    time_info: Dict[str, Any],
    variables: Dict[str, tuple[str, str]],
    meters: Dict[str, str],
    actuators: Dict[str, tuple[str, str, str]],
    state_keys: list[str],
    non_state_metric_keys: list[str] | None = None,
) -> Dict[str, Any]:
    """
    Constructs a comprehensive observation dictionary containing:
    - Named state variables (from `variables`)
    - Meter readings (from `meters`)
    - Applied actuator values (from `actuators` and `action`)
    - Time info data (from `time_info`)
    - Optional non-state metrics excluded from the agent observation

    The order of `obs` must match the order of keys in `variables` + `meters`.
    The order of `action` must match the order of keys in `actuators`.
    `state_keys` should represent the agent-facing observation ordering.
    """
    ordered_metric_keys = list(variables.keys()) + list(meters.keys())
    metric_values = dict(zip(ordered_metric_keys, obs))
    action_values = dict(zip(actuators.keys(), action))
    info = {
        **metric_values,
        **time_info,
        **action_values,
        "state_keys": list(state_keys) + list(time_info.keys()),
        "action_keys": list(actuators.keys()),
    }

    if non_state_metric_keys:
        info["non_state_metric_keys"] = list(non_state_metric_keys)
        info["non_state_metrics"] = {
            key: metric_values[key]
            for key in non_state_metric_keys
            if key in metric_values
        }

    return info
