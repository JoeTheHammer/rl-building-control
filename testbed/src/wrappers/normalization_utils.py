from typing import Any, SupportsFloat

import gymnasium
import numpy as np
from gymnasium.wrappers import NormalizeObservation, NormalizeReward
from sinergym.utils.wrappers import NormalizeAction
from stable_baselines3.common.vec_env import VecNormalize

from wrappers.discrete_action_wrapper import DiscreteActionWrapper


def _find_wrapper(env: Any, wrapper_class: type) -> Any:
    """
    Finds a wrapper of a specific class in a potentially complex
    environment stack, including custom adapters that hold envs as attributes.
    """
    # Create a list of environments to check, starting with the initial one
    env_queue = [env]
    # Keep track of visited environments to avoid infinite loops
    visited_envs = set()

    while env_queue:
        current_env = env_queue.pop(0)

        # Use object ID to check if we've seen this exact environment object before
        if id(current_env) in visited_envs:
            continue
        visited_envs.add(id(current_env))

        # Case 1: The current object is the wrapper we're looking for.
        if isinstance(current_env, wrapper_class):
            return current_env

        # Case 2: Special check for the VecNormalizeAdapter pattern.
        # Look inside for the `vec_env` attribute.
        if hasattr(current_env, "vec_env"):
            env_queue.append(current_env.vec_env)

        # Case 3: Standard gym wrapper, add the inner .env to the queue.
        if hasattr(current_env, "env"):
            env_queue.append(current_env.env)

    # If the queue is exhausted, and we haven't found the wrapper
    return None


def denormalize_state(state: Any, env: gymnasium.Env) -> Any:
    """
    Returns the denormalized state if a normalization wrapper is present.

    Searches for either a Stable-Baselines3 VecNormalize wrapper or a
    Gymnasium NormalizeObservation wrapper and applies the correct inverse
    normalization.
    """
    # 1. First, check for the Stable-Baselines3 VecNormalize wrapper
    vec_normalize_wrapper = _find_wrapper(env, VecNormalize)
    if vec_normalize_wrapper is not None and vec_normalize_wrapper.norm_obs:
        return vec_normalize_wrapper.unnormalize_obs(state)

    # 2. If not found, check for the standard Gymnasium wrapper
    gym_normalize_wrapper = _find_wrapper(env, NormalizeObservation)
    if gym_normalize_wrapper is not None and hasattr(gym_normalize_wrapper, "obs_rms"):
        return (
            state * np.sqrt(gym_normalize_wrapper.obs_rms.var + gym_normalize_wrapper.epsilon)
            + gym_normalize_wrapper.obs_rms.mean
        )

    # 3. If neither wrapper is found, return the original state
    return state


def denormalize_reward(reward: SupportsFloat, env: gymnasium.Env) -> SupportsFloat:
    vec_normalize_wrapper = _find_wrapper(env, VecNormalize)
    if vec_normalize_wrapper is not None and vec_normalize_wrapper.norm_reward:
        return vec_normalize_wrapper.unnormalize_reward(reward)

    norm_rew = _find_wrapper(env, NormalizeReward)
    if norm_rew is not None and hasattr(norm_rew, "return_rms"):
        scale = np.sqrt(norm_rew.return_rms.var + norm_rew.epsilon)
        return reward * scale

    return reward



def get_original_action(action: Any, env: gymnasium.Env) -> Any:
    action_normalize_wrapper = _find_wrapper(env, NormalizeAction)
    discrete_action_wrapper = _find_wrapper(env, DiscreteActionWrapper)
    if action_normalize_wrapper is not None:
        action = action_normalize_wrapper.reverting_action(action)

    if discrete_action_wrapper is not None:
        action = discrete_action_wrapper.get_energy_plus_action(action)

    return action
