import importlib
import os
from dataclasses import dataclass
from parser.config_parser import parse_sinergym_environment_config
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box
from sinergym import BaseReward

from custom_loggers.setup_logger import logger
from environments.base_provider import EnvironmentProvider
from environments.sinergym_config import SinergymEnvironmentConfig
from environments.sinergym_env import SinergymEnvironment
from reward.custom_reward import MyReward
from reward.expression_reward import ExpressionReward


@dataclass
class EnvironmentElements:
    building_model_path: str
    weather_data_path: str
    variables: Dict[str, Tuple[str, str]]
    meters: Dict[str, str]
    actuators: Dict[str, Tuple[str, str, str]]
    reward_function_cls: type[BaseReward]
    reward_variables: List[str]
    reward_kwargs: Optional[Dict[str, Any]]
    action_space: Box


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


def _parse_actuators(config: SinergymEnvironmentConfig) -> dict:
    return {
        name: (a.component, a.control_type, a.actuator_key)
        for name, a in config.action_space.actuators.items()
    }


def _build_action_space(config: SinergymEnvironmentConfig) -> Box:
    low, high = [], []

    for name, a in config.action_space.actuators.items():
        if a.type == "continuous":
            if a.range is None or len(a.range) != 2:
                raise ValueError(f"Actuator '{name}' requires a 'range' of two floats.")
            low.append(a.range[0])
            high.append(a.range[1])
        elif a.type == "discrete":
            logger.warning("Discrete actuator not yet supported and will be ignored.")
        else:
            raise ValueError(f"Unsupported actuator type: {a.type}")

    if not low:
        return gym.spaces.Box(low=0, high=0, shape=(0,), dtype=np.float32)

    return gym.spaces.Box(
        low=np.array(low, dtype=np.float32),
        high=np.array(high, dtype=np.float32),
        dtype=np.float32,
    )


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

    return MyReward, {}, reward_variables  # fallback


def _build_environment_elements(config: SinergymEnvironmentConfig) -> EnvironmentElements:
    building_model_path, weather_data_path = _resolve_paths(config)
    variables = _parse_variables(config)
    meters = _parse_meters(config)
    actuators = _parse_actuators(config)
    action_space = _build_action_space(config)
    reward_function_cls, reward_kwargs, reward_variables = _build_reward_function(config)

    return EnvironmentElements(
        building_model_path=building_model_path,
        weather_data_path=weather_data_path,
        variables=variables,
        meters=meters,
        actuators=actuators,
        reward_function_cls=reward_function_cls,
        reward_variables=reward_variables,
        reward_kwargs=reward_kwargs,
        action_space=action_space,
    )


class SinergymProvider(EnvironmentProvider):

    def create_environment(self, config_path: str) -> SinergymEnvironment:
        config = parse_sinergym_environment_config(config_path)
        env_elements = _build_environment_elements(config)

        return SinergymEnvironment(
            env_elements.building_model_path,
            env_elements.weather_data_path,
            env_elements.variables,
            env_elements.meters,
            env_elements.actuators,
            env_elements.reward_variables,
            env_elements.reward_function_cls,
            env_elements.reward_kwargs,
            env_elements.action_space,
        )
