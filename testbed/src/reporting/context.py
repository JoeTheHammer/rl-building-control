from __future__ import annotations

from copy import deepcopy
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

        env_files, original_environment_yaml = self._collect_environment_files()
        files.extend(env_files)

        controller_file = self._collect_controller_file()
        if controller_file:
            files.append(controller_file)

        if original_environment_yaml is not None:
            files.extend(self._collect_environment_resources(original_environment_yaml))

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

        original_data = deepcopy(data)

        sanitized_data = self._sanitize_environment_config(deepcopy(data))
        sanitized_yaml = yaml.safe_dump(sanitized_data, sort_keys=False, allow_unicode=True)

        file = ContextFile(
            relative_path="configs/environment.yaml",
            content=sanitized_yaml.encode("utf-8"),
            original_path=str(env_path),
            is_text=True,
        )

        return [file], original_data

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
        if path.is_absolute():
            return path.resolve()

        candidate_bases: list[Path] = []
        if base is not None:
            candidate_bases.append(base)
            # Include parents to support configs that already include the
            # context/ prefix when reproduced into a new suite directory.
            candidate_bases.extend(parent for parent in base.parents)
        candidate_bases.append(Path.cwd())

        for candidate_base in candidate_bases:
            resolved = (candidate_base / path).resolve()
            if resolved.exists():
                return resolved

        fallback_base = base if base is not None else Path.cwd()
        return (fallback_base / path).resolve()

    @staticmethod
    def _sanitize_environment_config(data: dict) -> dict:
        if not isinstance(data, dict):
            return data

        def _context_path(subdir: str, value: str) -> str:
            filename = Path(value).name
            return str(Path("context") / "resources" / subdir / filename)

        building = data.get("building_model")
        if isinstance(building, str) and building:
            data["building_model"] = _context_path("buildings", building)

        weather = data.get("weather_data")
        if isinstance(weather, str) and weather:
            data["weather_data"] = _context_path("weather", weather)

        return data


def collect_experiment_context(
    suite_config_path: str, experiment_config: ExperimentConfig
) -> ExperimentContext:
    collector = ExperimentContextCollector(suite_config_path, experiment_config)
    return collector.collect()
