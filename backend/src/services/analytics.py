from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import h5py
import numpy as np
from fastapi import HTTPException

from models.analytics import (
    AnalyticsDataResponse,
    AnalyticsEpisode,
    AnalyticsEvaluation,
    AnalyticsExperiment,
    AnalyticsSuiteSummary,
    AnalyticsTraining,
)
from services.experiment_suite import manager as suite_manager


def _ensure_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception:  # pragma: no cover - defensive
            return value.decode("utf-8", errors="ignore")
    if isinstance(value, np.ndarray):
        return [_ensure_scalar(item) for item in value.tolist()]
    if isinstance(value, list):
        return [_ensure_scalar(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _ensure_scalar(val) for key, val in value.items()}
    return value


def _read_metadata(obj: h5py.Group | h5py.File) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    for key, value in obj.attrs.items():
        metadata[str(key)] = _ensure_scalar(value)
    return metadata


def _read_string_dataset(dataset: h5py.Dataset | None) -> List[str]:
    if dataset is None:
        return []
    data = dataset.asstr()[()]
    if isinstance(data, np.ndarray):
        return [str(item) for item in data.tolist()]
    if isinstance(data, (list, tuple)):
        return [str(item) for item in data]
    if isinstance(data, (str, bytes, np.generic)):
        value = data if isinstance(data, str) else str(_ensure_scalar(data))
        return [value]
    return []


def _read_reward_dataset(dataset: h5py.Dataset | None) -> List[float]:
    if dataset is None:
        return []
    data = np.asarray(dataset[()])
    if data.size == 0:
        return []
    flattened = data.reshape(-1)
    return [float(_ensure_scalar(value)) for value in flattened.tolist()]


def _build_series_map(
    dataset: h5py.Dataset | None,
    names: Iterable[str],
    prefix: str,
) -> Dict[str, List[float]]:
    if dataset is None:
        return {}

    data = np.asarray(dataset[()])
    if data.size == 0:
        return {}

    if data.ndim == 1:
        data = data.reshape(-1, 1)

    columns = data.T
    resolved_names = list(names)

    series: Dict[str, List[float]] = {}
    for index, column in enumerate(columns):
        key = resolved_names[index] if index < len(resolved_names) else f"{prefix}_{index + 1:02d}"
        values = [float(_ensure_scalar(value)) for value in column.tolist()]
        series[key] = values
    return series


def _parse_training_group(group: h5py.Group) -> AnalyticsTraining:
    metadata = _read_metadata(group)
    action_names = _read_string_dataset(group.get("action_names"))
    state_names = _read_string_dataset(group.get("state_names"))
    reward = _read_reward_dataset(group.get("rewards"))
    actions = _build_series_map(group.get("actions"), action_names, "action")
    states = _build_series_map(group.get("states"), state_names, "state")

    return AnalyticsTraining(
        action_names=action_names,
        state_names=state_names,
        reward=reward,
        actions=actions,
        states=states,
        metadata=metadata,
    )


def _parse_episode_group(
    key: str,
    group: h5py.Group,
    default_action_names: Iterable[str],
    default_state_names: Iterable[str],
) -> AnalyticsEpisode:
    metadata = _read_metadata(group)
    action_names = _read_string_dataset(group.get("action_names")) or list(default_action_names)
    state_names = _read_string_dataset(group.get("state_names")) or list(default_state_names)
    reward = _read_reward_dataset(group.get("rewards"))
    actions = _build_series_map(group.get("actions"), action_names, "action")
    states = _build_series_map(group.get("states"), state_names, "state")

    label = metadata.get("name") or metadata.get("label")
    if label is None:
        episode_index = metadata.get("episode_index")
        if episode_index is not None:
            label = f"Episode {episode_index}"
        else:
            label = key.replace("_", " ").title()

    return AnalyticsEpisode(
        id=key,
        label=str(label) if label is not None else None,
        reward=reward,
        actions=actions,
        states=states,
        metadata=metadata,
    )


def _parse_evaluation_group(group: h5py.Group) -> AnalyticsEvaluation:
    metadata = _read_metadata(group)
    action_names = _read_string_dataset(group.get("action_names"))
    state_names = _read_string_dataset(group.get("state_names"))

    episodes: List[AnalyticsEpisode] = []
    for key, item in sorted(group.items()):
        if isinstance(item, h5py.Group) and key.startswith("episode"):
            episodes.append(_parse_episode_group(key, item, action_names, state_names))

    return AnalyticsEvaluation(
        action_names=action_names,
        state_names=state_names,
        episodes=episodes,
        metadata=metadata,
    )


def _parse_experiment_group(key: str, group: h5py.Group) -> AnalyticsExperiment:
    metadata = _read_metadata(group)
    name = metadata.get("name") or metadata.get("experiment") or key

    evaluation_group = group.get("evaluation")
    training_group = group.get("training")

    evaluation = (
        _parse_evaluation_group(evaluation_group)
        if isinstance(evaluation_group, h5py.Group)
        else None
    )
    training = (
        _parse_training_group(training_group)
        if isinstance(training_group, h5py.Group)
        else None
    )

    return AnalyticsExperiment(
        key=key,
        name=str(name),
        metadata=metadata,
        evaluation=evaluation,
        training=training,
    )


def _find_h5_file(directory: Path) -> Path:
    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=404, detail="Experiment suite directory not found")

    candidates = sorted(directory.glob("*.h5"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(status_code=404, detail="No HDF5 export found for the selected suite")
    return candidates[0]


def _load_hdf5_content(file_path: Path) -> tuple[Dict[str, Any], List[AnalyticsExperiment]]:
    metadata: Dict[str, Any] = {}
    experiments: List[AnalyticsExperiment] = []

    with h5py.File(file_path, "r") as handle:
        metadata = _read_metadata(handle)
        for key, item in handle.items():
            if isinstance(item, h5py.Group) and key.startswith("experiment"):
                experiments.append(_parse_experiment_group(key, item))

    return metadata, experiments


def list_available_suites() -> List[AnalyticsSuiteSummary]:
    summaries: List[AnalyticsSuiteSummary] = []
    for suite in suite_manager.list_suites():
        has_data = False
        file_name: str | None = None
        if suite.path:
            path = Path(suite.path).expanduser()
            try:
                file_path = _find_h5_file(path)
            except HTTPException:
                has_data = False
            else:
                has_data = True
                file_name = file_path.name

        summaries.append(
            AnalyticsSuiteSummary(
                id=suite.id,
                name=suite.name,
                status=suite.status,
                path=suite.path,
                config_filename=suite.config_filename,
                has_data=has_data,
                file_name=file_name,
            )
        )

    return summaries


def get_suite_file_path(suite_id: int) -> Path:
    suite = suite_manager.get_suite(suite_id)
    if not suite.path:
        raise HTTPException(status_code=404, detail="The selected suite does not contain exported data")

    directory = Path(suite.path).expanduser()
    return _find_h5_file(directory)


def load_suite_data(suite_id: int) -> AnalyticsDataResponse:
    suite = suite_manager.get_suite(suite_id)
    file_path = get_suite_file_path(suite_id)
    metadata, experiments = _load_hdf5_content(file_path)

    return AnalyticsDataResponse(
        suite_id=suite.id,
        suite_name=suite.name,
        file_name=file_path.name,
        metadata=metadata,
        experiments=experiments,
    )
