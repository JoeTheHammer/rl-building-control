from pathlib import Path

import yaml

from environments.sinergym_config import SinergymEnvironmentConfig
from experiment.experiment_config import ExperimentList


def parse_experiment_list(config_path: str) -> ExperimentList:
    """
    Parses a YAML configuration file containing a list of experiments.

    @param config_path: Path to the YAML file defining experiments.
    @type config_path: str

    @raises FileNotFoundError: If the YAML file does not exist.
    @raises yaml.YAMLError: If the YAML content is malformed.
    @raises pydantic.ValidationError: If the content does not match the expected schema.

    @return: An ExperimentList object containing all parsed experiments.
    @rtype: ExperimentList
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"{config_path} not found")

    with path.open("r") as f:
        data = yaml.safe_load(f)

    return ExperimentList(**data)


def parse_sinergym_environment_config(config_path: str) -> SinergymEnvironmentConfig:
    """
    Parses a YAML configuration file containing a Sinergym environment definition.

    @param config_path: Path to the YAML file defining a Sinergym environment.
    @type config_path: str

    @raises FileNotFoundError: If the YAML file does not exist.
    @raises yaml.YAMLError: If the YAML content is malformed.
    @raises pydantic.ValidationError: If the content does not match the expected schema.

    @return: A SinergymEnvironmentConfig object with all environment parameters loaded.
    @rtype: SinergymEnvironmentConfig
    """
    if not Path(config_path).is_file():
        raise FileNotFoundError(f"{config_path} not found")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return SinergymEnvironmentConfig(**data)
