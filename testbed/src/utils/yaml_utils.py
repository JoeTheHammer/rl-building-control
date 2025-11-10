from logging import Logger
from pathlib import Path
from typing import Any

import yaml
import os

def resolve_project_path(path: str) -> str:
    """
    Normalize a config or data path so it works both locally and inside Docker.

    - On the host: uses absolute or existing paths as-is.
    - Inside Docker: maps host-style paths (/home/.../config) to mounted volumes (/config, /data).
    """
    p = Path(path).expanduser()

    # If path already exists, no need to modify
    if p.exists():
        return str(p.resolve())

    # Detect if running inside a Docker container
    in_docker = Path("/.dockerenv").exists() or os.getenv("RUNNING_IN_DOCKER") == "1"
    if not in_docker:
        # On the host, try to resolve relative to project root
        project_root = Path(__file__).resolve().parents[3]
        candidate = (project_root / p).resolve()
        return str(candidate) if candidate.exists() else str(p)

    # Inside Docker: remap known prefixes
    path_str = str(p)
    if "config" in path_str:
        return str(Path("/config" + path_str.split("config", 1)[1]).resolve())
    if "data" in path_str:
        return str(Path("/data" + path_str.split("data", 1)[1]).resolve())

    # Fallback: just return the same
    return str(p)


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
