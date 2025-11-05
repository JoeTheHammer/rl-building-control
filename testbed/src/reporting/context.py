from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import yaml

from experiment.experiment_config import ExperimentConfig


@dataclass(frozen=True)
class ContextFile:
    """Represents a file that should be embedded into the HDF5 export."""

    relative_path: str
    content: bytes
    original_path: Optional[str] = None
    is_text: bool = False
    metadata: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class ExperimentContext:
    """Collection of files required to reproduce an experiment."""

    files: List[ContextFile]


class ExperimentContextCollector:
    """Utility that gathers configuration and resource files for an experiment."""

    def __init__(self, suite_config_path: str, experiment_config: ExperimentConfig) -> None:
        self._suite_config_path = Path(suite_config_path).expanduser().resolve()
        self._experiment_config = experiment_config

    def collect(self) -> ExperimentContext:
        files: list[ContextFile] = []

        files.extend(self._collect_experiment_configs())

        env_files, environment_yaml = self._collect_environment_files()
        files.extend(env_files)

        controller_file = self._collect_controller_file()
        if controller_file:
            files.append(controller_file)

        if environment_yaml is not None:
            files.extend(self._collect_environment_resources(environment_yaml))

        return ExperimentContext(files=files)

    def _collect_experiment_configs(self) -> Iterable[ContextFile]:
        experiment_yaml = self._suite_config_path.read_text(encoding="utf-8")

        entry_dict = self._experiment_config.model_dump(exclude_none=True)
        entry_yaml = yaml.safe_dump({"experiments": [entry_dict]}, sort_keys=False, allow_unicode=True)

        yield ContextFile(
            relative_path="configs/experiment.yaml",
            content=experiment_yaml.encode("utf-8"),
            original_path=str(self._suite_config_path),
            is_text=True,
        )

        yield ContextFile(
            relative_path="configs/experiment_entry.yaml",
            content=entry_yaml.encode("utf-8"),
            original_path=None,
            is_text=True,
        )

    def _collect_environment_files(self) -> tuple[List[ContextFile], Optional[dict]]:
        path_value = self._experiment_config.environment_config
        if not path_value:
            return [], None

        env_path = self._resolve_path(path_value, base=self._suite_config_path.parent)
        if not env_path.is_file():
            raise FileNotFoundError(f"Environment config not found: {env_path}")

        content = env_path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid environment YAML at {env_path}: {exc}") from exc

        file = ContextFile(
            relative_path="configs/environment.yaml",
            content=content.encode("utf-8"),
            original_path=str(env_path),
            is_text=True,
        )

        return [file], data

    def _collect_controller_file(self) -> Optional[ContextFile]:
        path_value = self._experiment_config.controller_config
        if not path_value:
            return None

        controller_path = self._resolve_path(path_value, base=self._suite_config_path.parent)
        if not controller_path.is_file():
            raise FileNotFoundError(f"Controller config not found: {controller_path}")

        content = controller_path.read_text(encoding="utf-8")
        return ContextFile(
            relative_path="configs/controller.yaml",
            content=content.encode("utf-8"),
            original_path=str(controller_path),
            is_text=True,
        )

    def _collect_environment_resources(self, data: dict) -> Iterable[ContextFile]:
        building = data.get("building_model")
        weather = data.get("weather_data")

        if building:
            building_path = self._resolve_path(building)
            if not building_path.is_file():
                raise FileNotFoundError(f"Building model not found: {building_path}")
            yield ContextFile(
                relative_path=f"resources/buildings/{building_path.name}",
                content=building_path.read_bytes(),
                original_path=str(building_path),
                metadata={"resource_type": "building_model"},
            )

        weather_path: Optional[Path] = None
        if weather:
            weather_path = self._resolve_path(weather)
            if not weather_path.is_file():
                raise FileNotFoundError(f"Weather file not found: {weather_path}")
            yield ContextFile(
                relative_path=f"resources/weather/{weather_path.name}",
                content=weather_path.read_bytes(),
                original_path=str(weather_path),
                metadata={"resource_type": "weather_epw"},
            )

        ddy_candidates: Iterable[Path] = []
        if weather_path:
            ddy_candidates = weather_path.parent.glob("*.ddy")

        for ddy_path in ddy_candidates:
            if ddy_path.is_file():
                yield ContextFile(
                    relative_path=f"resources/weather/{ddy_path.name}",
                    content=ddy_path.read_bytes(),
                    original_path=str(ddy_path),
                    metadata={"resource_type": "weather_ddy"},
                )

    @staticmethod
    def _resolve_path(raw: str, base: Optional[Path] = None) -> Path:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            if base is None:
                base = Path.cwd()
            path = (base / path).resolve()
        else:
            path = path.resolve()
        return path


def collect_experiment_context(
    suite_config_path: str, experiment_config: ExperimentConfig
) -> ExperimentContext:
    collector = ExperimentContextCollector(suite_config_path, experiment_config)
    return collector.collect()
