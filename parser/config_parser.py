from pathlib import Path
from typing import List

import yaml

from custom_loggers.setup_logger import logger
from simulation.experiment import ExperimentConfig


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
    config_file = Path(config_path)

    # Check if file exists
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_file}")
        raise FileNotFoundError(f"Config file not found: {config_file}")

    # Check file extension
    if config_file.suffix not in [".yaml", ".yml"]:
        logger.error(f"Invalid file extension: {config_file.suffix}. Expected .yaml or .yml")
        raise ValueError("Provided file is not a valid YAML file.")

    # Load YAML content
    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        raise

    # Validate structure
    if "experiments" not in data or not isinstance(data["experiments"], list):
        logger.error("YAML does not contain a list under 'experiments'.")
        raise ValueError("Invalid YAML structure. Expected a top-level 'experiments' list.")

    experiments: List[ExperimentConfig] = []

    for idx, entry in enumerate(data["experiments"]):
        try:
            name = entry["name"]
            engine = entry["engine"]
            environment_config = entry["environment_config"]
            experiments.append(ExperimentConfig(name, engine, environment_config))
        except KeyError as e:
            logger.error(f"Missing field {e} in experiment #{idx + 1}")
            raise ValueError(f"Experiment #{idx + 1} is missing required field: {e}")

    logger.info(f"Successfully parsed {len(experiments)} experiment configurations.")
    return experiments
