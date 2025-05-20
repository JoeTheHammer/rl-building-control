from logging import Logger
from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(file_path: str, logger: Logger) -> Any:
    """
    Loads and parses a YAML file after validating its existence and extension.

    Args:
        file_path (str): Path to the YAML file.
        logger (Logger): Logger to be used.

    Returns:
        Any: Parsed YAML content (usually a dict).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is invalid.
        yaml.YAMLError: If the YAML is invalid.

    """
    config_file = Path(file_path)

    if not config_file.exists():
        logger.error(f"YAML file not found: {config_file}")
        raise FileNotFoundError(f"Config file not found: {config_file}")

    if config_file.suffix not in [".yaml", ".yml"]:
        logger.error(f"Invalid file extension: {config_file.suffix}. Expected .yaml or .yml")
        raise ValueError("Provided file is not a valid YAML file.")

    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        raise

    return data
