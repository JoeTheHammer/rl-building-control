import os
from parser.config_parser import parse_sinergym_environment_config
from typing import Tuple

import gymnasium as gym
import numpy as np
from custom_loggers.setup_logger import logger
from environments.base_provider import EnvironmentProvider
from environments.sinergym_config import SinergymEnvironmentConfig
from environments.sinergym_env import SinergymEnvironment


def _build_environment_elements(config: SinergymEnvironmentConfig) -> Tuple:
    """
    Converts a SinergymEnvironmentConfig object into the concrete elements needed
    to initialize a Sinergym environment.

    Returns:
        Tuple containing:
            - idf_path (str): Absolute path to the building model file
            - epw_path (str): Absolute path to the weather data file
            - variables (dict): Observation variables as (type, zone) tuples
            - meters (dict): Dictionary of meter names
            - actuators (dict): Actuator definitions as (component, control_type, actuator_key) tuples
            - action_space (gym.Space): Combined Gym action space for all actuators
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    building_model_path = os.path.join(project_root, config.building_model)
    weather_data_path = os.path.join(project_root, config.weather_data)

    variables = {key: (v.type, v.zone) for key, v in config.state_space.variables.items()}

    meters = config.state_space.meters

    actuators = {
        name: (a.component, a.control_type, a.actuator_key)
        for name, a in config.action_space.actuators.items()
    }

    # Build flat action space from all continuous actuators
    low = []
    high = []

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

    # Create flat Box action space
    if not low:
        action_space = gym.spaces.Box(low=0, high=0, shape=(0,), dtype=np.float32)
    else:
        action_space = gym.spaces.Box(
            low=np.array(low, dtype=np.float32),
            high=np.array(high, dtype=np.float32),
            dtype=np.float32,
        )

    return building_model_path, weather_data_path, variables, meters, actuators, action_space


class SinergymProvider(EnvironmentProvider):

    def create_environment(self, config_path: str) -> SinergymEnvironment:
        config = parse_sinergym_environment_config(config_path)
        building_model_path, weather_data_path, variables, meters, actuators, action_space = (
            _build_environment_elements(config)
        )
        return SinergymEnvironment(
            building_model_path, weather_data_path, variables, meters, actuators, action_space
        )
