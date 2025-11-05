from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, Optional

import h5py
import numpy as np

from reporting.context import ContextFile, ExperimentContext


def _ensure_directory(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def _sanitize_name(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip())
    return sanitized.strip("_") or "experiment"


def _append_dataset(group: h5py.Group, name: str, data: np.ndarray) -> h5py.Dataset:
    if name in group:
        dataset = group[name]
        dataset.resize(dataset.shape[0] + data.shape[0], axis=0)
        dataset[-data.shape[0] :] = data
        return dataset

    maxshape = (None,) + data.shape[1:]
    return group.create_dataset(
        name,
        data=data,
        maxshape=maxshape,
        chunks=True,
        compression="gzip",
    )


def _store_metadata(
    target: h5py.Group | h5py.File, metadata: Optional[Dict[str, Any]] = None
) -> None:
    if not metadata:
        return

    for key, value in metadata.items():
        if value is None:
            continue
        target.attrs[key] = value


class BaseStorageHandler:
    def __init__(self, group: h5py.Group):
        self.group = group
        self._state_names_written = False
        self._action_names_written = False
        self._finalized = False

    def set_metadata(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        _store_metadata(self.group, metadata)

    def set_state_names(self, names: Optional[Iterable[str]]) -> None:
        if not names or "state_names" in self.group:
            return
        string_dtype = h5py.string_dtype(encoding="utf-8")
        self.group.create_dataset("state_names", data=np.array(list(names), dtype=string_dtype))

    def set_action_names(self, names: Optional[Iterable[str]]) -> None:
        if not names or "action_names" in self.group:
            return
        string_dtype = h5py.string_dtype(encoding="utf-8")
        self.group.create_dataset("action_names", data=np.array(list(names), dtype=string_dtype))

    def set_non_state_metric_names(self, names: Optional[Iterable[str]]) -> None:
        if not names or "non_state_metric_names" in self.group:
            return
        string_dtype = h5py.string_dtype(encoding="utf-8")
        self.group.create_dataset(
            "non_state_metric_names",
            data=np.array(list(names), dtype=string_dtype),
        )

    def on_start(self) -> None:
        if "started_at" not in self.group.attrs:
            self.group.attrs["started_at"] = datetime.utcnow().isoformat()

    def finalize(self) -> None:
        if self._finalized:
            return
        self.group.attrs["finished_at"] = datetime.utcnow().isoformat()
        self._finalized = True


class TrainingStorageHandler(BaseStorageHandler):
    def __init__(self, group: h5py.Group):
        super().__init__(group)
        self._datasets: Dict[str, h5py.Dataset] = {}
        self.total_steps = 0
        self.total_reward = 0.0

    def record_chunk(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        non_state_metrics: np.ndarray | None = None,
    ) -> None:
        if rewards.size == 0:
            return

        states = np.asarray(states)
        actions = np.asarray(actions)
        rewards = np.asarray(rewards)
        metrics = np.asarray(non_state_metrics) if non_state_metrics is not None else None

        if states.ndim == 1:
            states = states.reshape(-1, 1)
        if actions.ndim == 1:
            actions = actions.reshape(-1, 1)
        if rewards.ndim == 1:
            rewards = rewards.reshape(-1, 1)
        if metrics is not None and metrics.ndim == 1:
            metrics = metrics.reshape(-1, 1)

        self._datasets["states"] = _append_dataset(self.group, "states", states)
        self._datasets["actions"] = _append_dataset(self.group, "actions", actions)
        self._datasets["rewards"] = _append_dataset(self.group, "rewards", rewards)
        if metrics is not None and metrics.size:
            self._datasets["non_state_metrics"] = _append_dataset(
                self.group, "non_state_metrics", metrics
            )

        self.total_steps += rewards.shape[0]
        self.total_reward += float(rewards.sum())

    def finalize(self) -> None:
        self.group.attrs["total_steps"] = self.total_steps
        self.group.attrs["total_reward"] = self.total_reward
        super().finalize()


class EvaluationStorageHandler(BaseStorageHandler):
    def __init__(self, group: h5py.Group):
        super().__init__(group)
        self._current_episode_group: Optional[h5py.Group] = None
        self._episode_datasets: Dict[str, h5py.Dataset] = {}
        self._episode_steps = 0
        self._episode_reward = 0.0
        self._episode_counter = 0
        self._total_reward = 0.0

    def start_episode(self, index: int, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._current_episode_group is not None:
            raise RuntimeError("Previous episode has not been finalized before starting a new one.")

        group_name = f"episode_{index:03d}"
        self._current_episode_group = self.group.create_group(group_name)
        self._episode_datasets = {}
        self._episode_steps = 0
        self._episode_reward = 0.0
        self._episode_counter += 1

        episode_group = self._current_episode_group
        episode_group.attrs["episode_index"] = index
        episode_group.attrs["created_at"] = datetime.utcnow().isoformat()
        _store_metadata(episode_group, metadata)

    def record_chunk(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        non_state_metrics: np.ndarray | None = None,
    ) -> None:
        if self._current_episode_group is None:
            raise RuntimeError("Cannot record data without an active episode.")
        if rewards.size == 0:
            return

        states = np.asarray(states)
        actions = np.asarray(actions)
        rewards = np.asarray(rewards)
        metrics = np.asarray(non_state_metrics) if non_state_metrics is not None else None

        if states.ndim == 1:
            states = states.reshape(-1, 1)
        if actions.ndim == 1:
            actions = actions.reshape(-1, 1)
        if rewards.ndim == 1:
            rewards = rewards.reshape(-1, 1)
        if metrics is not None and metrics.ndim == 1:
            metrics = metrics.reshape(-1, 1)

        group = self._current_episode_group
        self._episode_datasets["states"] = _append_dataset(group, "states", states)
        self._episode_datasets["actions"] = _append_dataset(group, "actions", actions)
        self._episode_datasets["rewards"] = _append_dataset(group, "rewards", rewards)
        if metrics is not None and metrics.size:
            self._episode_datasets["non_state_metrics"] = _append_dataset(
                group, "non_state_metrics", metrics
            )

        steps = rewards.shape[0]
        self._episode_steps += steps
        self._episode_reward += float(rewards.sum())
        self._total_reward += float(rewards.sum())

    def finalize_episode(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._current_episode_group is None:
            return

        episode_group = self._current_episode_group
        episode_group.attrs["total_steps"] = self._episode_steps
        episode_group.attrs["total_reward"] = self._episode_reward
        if metadata:
            _store_metadata(episode_group, metadata)
        episode_group.attrs["finished_at"] = datetime.utcnow().isoformat()

        self._current_episode_group = None
        self._episode_datasets = {}
        self._episode_steps = 0
        self._episode_reward = 0.0

    def finalize(self) -> None:
        self.group.attrs["episodes"] = self._episode_counter
        self.group.attrs["total_reward"] = self._total_reward
        super().finalize()


class ExperimentStorage:
    def __init__(self, group: h5py.Group):
        self.group = group
        self.training_group = group.require_group("training")
        self.evaluation_group = group.require_group("evaluation")

    def create_training_handler(self) -> TrainingStorageHandler:
        return TrainingStorageHandler(self.training_group)

    def create_evaluation_handler(self) -> EvaluationStorageHandler:
        return EvaluationStorageHandler(self.evaluation_group)

    def update_metadata(self, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        combined = dict(metadata or {})
        combined.update({k: v for k, v in kwargs.items() if v is not None})
        _store_metadata(self.group, combined)

    def store_context(self, context: ExperimentContext) -> None:
        context_group = self.group.require_group("context")
        for context_file in context.files:
            self._store_context_file(context_group, context_file)

    def _store_context_file(self, base_group: h5py.Group, context_file: ContextFile) -> None:
        path = PurePosixPath(context_file.relative_path)
        group = base_group
        for part in path.parts[:-1]:
            group = group.require_group(part)

        name = path.name
        if context_file.is_text:
            dtype = h5py.string_dtype(encoding="utf-8")
            data = context_file.content.decode("utf-8")
            dataset = group.create_dataset(name, data=np.array(data, dtype=dtype), dtype=dtype)
        else:
            dataset = group.create_dataset(
                name,
                data=np.frombuffer(context_file.content, dtype=np.uint8),
            )

        dataset.attrs["relative_path"] = str(path)
        dataset.attrs["is_text"] = bool(context_file.is_text)
        if context_file.original_path:
            dataset.attrs["original_path"] = context_file.original_path
        if context_file.metadata:
            for key, value in context_file.metadata.items():
                if value is not None:
                    dataset.attrs[key] = value


class HDF5StorageManager:
    def __init__(self, file_path: str):
        _ensure_directory(file_path)
        self.file_path = file_path
        self._file = h5py.File(file_path, "w", libver="latest")
        self._file.swmr_mode = True
        self._file.attrs["created_at"] = datetime.utcnow().isoformat()
        self._file.attrs["schema_version"] = "1.1"

    def create_experiment(
        self,
        experiment_id: int,
        experiment_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExperimentStorage:
        group_name = f"experiment_{experiment_id:03d}_{_sanitize_name(experiment_name)}"
        group = self._file.create_group(group_name)
        base_metadata = {
            "name": experiment_name,
            "experiment_id": experiment_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        if metadata:
            base_metadata.update(metadata)
        _store_metadata(group, base_metadata)
        group.attrs["experiment"] = experiment_name

        return ExperimentStorage(group)

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None

    def flush(self) -> None:
        """Ensure all buffered data is written to disk (SWMR visible)."""
        if self._file:
            self._file.flush()
