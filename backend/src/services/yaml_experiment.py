from io import StringIO
from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from models.experiment import ExperimentConfig


yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True


def build_experiment_yaml(configs: Iterable[ExperimentConfig]) -> str:
    doc = CommentedMap()
    experiments_seq = CommentedSeq()

    for config in configs:
        experiment_map = CommentedMap()
        experiment_map["name"] = DoubleQuotedScalarString(config.name)
        experiment_map["engine"] = DoubleQuotedScalarString(config.engine)
        experiment_map["environment_config"] = DoubleQuotedScalarString(
            config.environmentConfig
        )
        experiment_map["controller"] = DoubleQuotedScalarString(config.controller)
        experiment_map["controller_config"] = DoubleQuotedScalarString(
            config.controllerConfig
        )
        experiment_map["episodes"] = config.episodes or 0

        reporting_map = CommentedMap()
        reporting_map["plots"] = bool(config.reporting.plots)
        reporting_map["denormalize_state"] = bool(
            config.reporting.denormalizeState
        )
        reporting_map["export"] = bool(config.reporting.export)
        experiment_map["reporting"] = reporting_map

        experiments_seq.append(experiment_map)

    doc["experiments"] = experiments_seq

    stream = StringIO()
    yaml.dump(doc, stream)
    return stream.getvalue()


def save_experiment_yaml(configs: Iterable[ExperimentConfig], filepath: Path) -> None:
    yaml_str = build_experiment_yaml(configs)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(yaml_str, encoding="utf-8")
