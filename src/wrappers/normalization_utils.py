from typing import Any

import gymnasium
import numpy as np
from gymnasium.wrappers import NormalizeObservation


def _find_wrapper(env, wrapper_type):
    """
    Recursively search for a specific wrapper in a nested environment.
    """
    while hasattr(env, "env"):
        if isinstance(env, wrapper_type):
            return env
        env = env.env
    return None


def denormalize_state(state: Any, env: gymnasium.Env) -> Any:
    """
    Returns the denormalized state if a normalization wrapper is present in the environment.

    Looks for a NormalizeObservation wrapper and applies inverse normalization using its
    running mean and variance. If no such wrapper is found, returns the original state.

    Parameters
    ----------
    state : Any
        The normalized state.

    env : gymnasium.Env
        The (possibly wrapped) Gymnasium environment.

    Returns
    -------
    Any
        Denormalized state or original input if no normalization was applied.
    """
    normalize_wrapper = _find_wrapper(env, NormalizeObservation)  # or VecNormalize for SB3

    if (
        normalize_wrapper is not None
        and hasattr(normalize_wrapper, "obs_rms")
        and hasattr(normalize_wrapper, "epsilon")
    ):
        denorm_state = (
            state * np.sqrt(normalize_wrapper.obs_rms.var + normalize_wrapper.epsilon)
            + normalize_wrapper.obs_rms.mean
        )
        return denorm_state

    return state
