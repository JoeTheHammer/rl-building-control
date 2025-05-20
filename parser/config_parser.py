from typing import Dict, List

from custom_loggers.setup_logger import logger as setup_logger
from environments.sinergym_env import SinergymEnvironmentConfig
from simulation.experiment import ExperimentConfig
from utils.yaml_utils import load_yaml_file


def parse_experiment_configs(config_path: str) -> List[ExperimentConfig]:
    """
    Parses a YAML file containing a list of experiment configurations.

    Args:
        config_path (str): Path to the YAML configuration file.

    Returns:
        List[ExperimentConfig]: A list of validated experiment configurations.

    Logs:
        - Error if file does not exist or has wrong extension.
        - Error if structure is invalid or required fields are missing.
    """
    data = load_yaml_file(config_path, setup_logger)

    if "experiments" not in data or not isinstance(data["experiments"], list):
        setup_logger.error("YAML does not contain a list under 'experiments'.")
        raise ValueError("Invalid YAML structure. Expected a top-level 'experiments' list.")

    experiments: List[ExperimentConfig] = []

    for idx, entry in enumerate(data["experiments"]):
        try:
            name = entry["name"]
            engine = entry["engine"]
            environment_config = entry["environment_config"]
            experiments.append(ExperimentConfig(name, engine, environment_config))
        except KeyError as e:
            setup_logger.error(f"Missing field {e} in experiment #{idx + 1}")
            raise ValueError(f"Experiment #{idx + 1} is missing required field: {e}")

    setup_logger.info(f"Successfully parsed {len(experiments)} experiment configurations.")
    return experiments


def parse_sinergym_environment_config(config_path: str) -> SinergymEnvironmentConfig:
    """
    Parses a YAML file containing sinergym environment configuration.

    Args:
        config_path (str): Path to the YAML configuration file.

    Returns:
        Dict[str, str]: Dictionary with keys 'building_model' and 'weather_data'.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is invalid or required fields are missing.
        yaml.YAMLError: If the YAML content is malformed.

    Logs:
        - Error if file is missing or invalid.
        - Error if YAML is not correctly structured.
        - Info on successful parsing.
    """
    data = load_yaml_file(config_path, setup_logger)

    try:
        building_model_path = data["building_model"]
        weather_data_path = data["weather_data"]
        setup_logger.info(f"Successfully parsed environment config from: {config_path}")
    except KeyError as e:
        setup_logger.error(f"Missing field {e} in environment data")
        raise ValueError(f"Missing field {e} in environment data")

    return SinergymEnvironmentConfig(building_model_path, weather_data_path)
