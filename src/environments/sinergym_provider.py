import importlib
import os
from dataclasses import dataclass
from parser.config_parser import parse_sinergym_environment_config
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

import gymnasium as gym
import numpy as np
from gymnasium.wrappers import NormalizeObservation
from sinergym import BaseReward

from environments.base_provider import IEnvironmentProvider
from environments.sinergym_config import SinergymEnvironmentConfig
from environments.sinergym_env import SinergymEnvironment
from reward.expression_reward import ExpressionReward
from spaces.custom_action_space import ActuatorActionSpace


@dataclass
class EnvironmentElements:
    building_model_path: str
    weather_data_path: str
    variables: Dict[str, Tuple[str, str]]
    meters: Dict[str, str]
    time_info: Optional[Dict[str, Dict[str, bool]]]
    actuators: Dict[str, Tuple[str, str, str]]
    reward_function_cls: type[BaseReward]
    reward_variables: List[str]
    reward_kwargs: Optional[Dict[str, Any]]
    action_space: ActuatorActionSpace
    config_params: Optional[Dict[str, Any]]


EXPRESSION_REWARD_TYPE = "expression"
PYTHON_REWARD_TYPE = "python"


def _resolve_paths(config: SinergymEnvironmentConfig) -> Tuple[str, str]:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    building_model_path = os.path.join(project_root, config.building_model)
    weather_data_path = os.path.join(project_root, config.weather_data)
    return building_model_path, weather_data_path


def _parse_variables(config: SinergymEnvironmentConfig) -> dict:
    return {key: (v.type, v.zone) for key, v in config.state_space.variables.items()}


def _parse_meters(config: SinergymEnvironmentConfig) -> dict:
    return config.state_space.meters


def _parse_time_info(config: SinergymEnvironmentConfig) -> Optional[Dict[str, Dict[str, bool]]]:
    if config.state_space.time_info is None:
        return None
    return {
        name: {"cyclic": bool(info.cyclic)} for name, info in config.state_space.time_info.items()
    }


def _parse_actuators(config: SinergymEnvironmentConfig) -> dict:
    return {
        name: (a.component, a.control_type, a.actuator_key)
        for name, a in config.action_space.actuators.items()
    }


def _build_action_space(config: SinergymEnvironmentConfig) -> ActuatorActionSpace:
    spaces = []
    discrete_mappings = []

    for name, a in config.action_space.actuators.items():
        if a.type == "continuous":
            if a.range is None or len(a.range) != 2:
                raise ValueError(f"Actuator '{name}' requires a 'range' of two floats.")
            space = gym.spaces.Box(
                low=np.array([a.range[0]], dtype=np.float32),
                high=np.array([a.range[1]], dtype=np.float32),
                dtype=np.float32,
            )
            spaces.append(space)
            discrete_mappings.append(None)

        elif a.type == "discrete":
            if a.values:
                values = a.values
            elif a.range and a.step_size:
                start, end = a.range
                values = [
                    round(start + i * a.step_size, 10)
                    for i in range(int((end - start) / a.step_size) + 1)
                ]
            else:
                raise ValueError(
                    f"Discrete actuator '{name}' must define 'values' or 'range' + 'step_size'."
                )
            space = gym.spaces.Discrete(len(values))
            spaces.append(space)
            discrete_mappings.append(values)

        else:
            raise ValueError(f"Unsupported actuator type: {a.type}")

    return ActuatorActionSpace(spaces, discrete_mappings)


def _build_episode(config: SinergymEnvironmentConfig) -> dict:
    """Parses and validates episode parameters from the config."""
    if not config.episode:
        return {}

    episode_params = {}
    if config.episode.timesteps_per_hour is not None:
        if config.episode.timesteps_per_hour <= 0:
            raise ValueError("timesteps_per_hour must be a positive integer.")
        episode_params["timesteps_per_hour"] = config.episode.timesteps_per_hour

    if config.episode.period is not None:
        if len(config.episode.period) != 6:
            raise ValueError(
                "period must contain exactly 6 integers for [start_day, start_month, start_year, end_day, end_month, end_year]."
            )
        # Sinergym expects a tuple for the period
        episode_params["runperiod"] = tuple(config.episode.period)

    return episode_params


def _build_reward_function(
    config: SinergymEnvironmentConfig,
) -> Tuple[Any, Dict[str, Any], List[str]]:
    reward_cfg = config.reward_function
    reward_variables = (
        reward_cfg.variables if hasattr(reward_cfg, "variables") and reward_cfg.variables else []
    )

    if reward_cfg.type == EXPRESSION_REWARD_TYPE:
        return (
            ExpressionReward,
            {
                "expression": reward_cfg.expression,
                "params": reward_cfg.params or {},
            },
            reward_variables,
        )

    elif reward_cfg.type == PYTHON_REWARD_TYPE:
        try:
            module = importlib.import_module(reward_cfg.module)
            cls = getattr(module, reward_cfg.class_name)
            return cls, reward_cfg.init_args or {}, reward_variables
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Could not import custom reward class '{reward_cfg.class_name}' "
                f"from module '{reward_cfg.module}': {e}"
            )

    raise Exception(f"Unsupported reward type '{reward_cfg.type}'")


def _build_environment_elements(config: SinergymEnvironmentConfig) -> EnvironmentElements:
    building_model_path, weather_data_path = _resolve_paths(config)
    variables = _parse_variables(config)
    meters = _parse_meters(config)
    actuators = _parse_actuators(config)
    time_info = _parse_time_info(config)
    action_space = _build_action_space(config)
    build_episode = _build_episode(config)
    reward_function_cls, reward_kwargs, reward_variables = _build_reward_function(config)

    return EnvironmentElements(
        building_model_path=building_model_path,
        weather_data_path=weather_data_path,
        variables=variables,
        meters=meters,
        actuators=actuators,
        time_info=time_info,
        reward_function_cls=reward_function_cls,
        reward_variables=reward_variables,
        reward_kwargs=reward_kwargs,
        action_space=action_space,
        config_params=build_episode,
    )


class SinergymProvider(IEnvironmentProvider):

    def create_environment(self, config_path: str) -> SinergymEnvironment | NormalizeObservation:
        config = parse_sinergym_environment_config(config_path)
        env_elements = _build_environment_elements(config)

        env = SinergymEnvironment(
            env_elements.building_model_path,
            env_elements.weather_data_path,
            env_elements.variables,
            env_elements.meters,
            env_elements.actuators,
            env_elements.reward_variables,
            env_elements.reward_function_cls,
            env_elements.action_space,
            env_elements.reward_kwargs,
            env_elements.time_info,
            env_elements.config_params,
        )

        if config.normalize_state:
            env = NormalizeObservation(env)

        return env
