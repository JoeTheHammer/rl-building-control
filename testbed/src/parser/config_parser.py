from pathlib import Path
from typing import Any

import yaml

LEGACY_REPORTING_FIELDS = {"plots", "export"}

from environments.sinergym_config import SinergymEnvironmentConfig
from experiment.experiment_config import ExperimentList


def parse_experiment_list(config_path: str) -> ExperimentList:
    """
    Parses a YAML configuration file containing a list of experiments.

    @param config_path: Path to the YAML file defining experiments.
    @type config_path: str

    @raises FileNotFoundError: If the YAML file does not exist.
    @raises yaml.YAMLError: If the YAML content is malformed.
    @raises ValueError: If legacy reporting fields are present in the configuration.
    @raises pydantic.ValidationError: If the content does not match the expected schema.

    @return: An ExperimentList object containing all parsed experiments.
    @rtype: ExperimentList
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"{config_path} not found")

    with path.open("r") as f:
        data = yaml.safe_load(f)

    _validate_reporting_fields(data)

    return ExperimentList(**data)


def _validate_reporting_fields(data: Any) -> None:
    if not isinstance(data, dict):
        return

    experiments = data.get("experiments")
    if not isinstance(experiments, list):
        return

    for index, experiment in enumerate(experiments, start=1):
        if not isinstance(experiment, dict):
            continue

        reporting = experiment.get("reporting")
        if not isinstance(reporting, dict):
            continue

        unsupported = LEGACY_REPORTING_FIELDS.intersection(reporting)
        if unsupported:
            fields = ", ".join(sorted(unsupported))
            raise ValueError(
                "Unsupported reporting fields found in experiment "
                f"#{index}: {fields}. Remove legacy reporting options from the configuration."
            )


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
