from __future__ import annotations

import math
import os
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, Optional, Sequence

import yaml

from parser.config_parser import parse_sinergym_environment_config

_STATUS_LOCK = Lock()
_STATUS_PATH = Path(os.getenv("EXPERIMENT_STATUS_FILE", Path.cwd() / "status.yaml"))
_CURRENT_EXPERIMENT_ID: Optional[int] = None


def _load_status() -> Dict[str, Any]:
    if _STATUS_PATH.exists():
        with _STATUS_PATH.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
            if isinstance(data, dict):
                return dict(data)
    return {}


def _write_status(data: Dict[str, Any]) -> None:
    _STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _STATUS_PATH.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _default_zero(value: Any) -> int:
    converted = _to_int(value)
    return converted if converted is not None else 0


def initialize_status(experiments: Sequence[Dict[str, Any]]) -> None:
    normalized: list[Dict[str, Any]] = []
    for entry in experiments:
        experiment_id = _to_int(entry.get("id"))
        if experiment_id is None:
            continue
        name_value = entry.get("name")
        name = str(name_value) if isinstance(name_value, str) else None
        total_eval = _to_int(entry.get("total_evaluation_episodes"))
        total_training = _to_int(entry.get("total_training_episodes"))
        normalized.append(
            {
                "id": experiment_id,
                "name": name,
                "status": "pending",
                "total_training_episodes": total_training,
                "current_training_episode": 0,
                "total_evaluation_episodes": total_eval,
                "current_evaluation_episode": 0,
            }
        )

    normalized.sort(key=lambda item: item["id"])
    with _STATUS_LOCK:
        _write_status({"experiments": normalized})
    set_current_experiment(None)


def set_current_experiment(experiment_id: Optional[int]) -> None:
    global _CURRENT_EXPERIMENT_ID
    if experiment_id is None:
        _CURRENT_EXPERIMENT_ID = None
        return
    converted = _to_int(experiment_id)
    _CURRENT_EXPERIMENT_ID = converted if converted is not None else None


def _update_current_experiment(
    updater: Callable[[Dict[str, Any]], bool | None]
) -> None:
    experiment_id = _CURRENT_EXPERIMENT_ID
    if experiment_id is None:
        return

    with _STATUS_LOCK:
        data = _load_status()
        experiments = data.get("experiments")
        if not isinstance(experiments, list):
            return

        for entry in experiments:
            if not isinstance(entry, dict):
                continue
            entry_id = _to_int(entry.get("id"))
            if entry_id == experiment_id:
                changed = updater(entry)
                if changed is False:
                    return
                data["experiments"] = experiments
                _write_status(data)
                return


def set_hyperparameter_tuning_status() -> None:
    def _updater(entry: Dict[str, Any]) -> bool:
        entry["status"] = "hyperparameter_tuning"
        return True

    _update_current_experiment(_updater)


def set_training_status(total_training_episodes: Optional[int] = None) -> None:
    def _updater(entry: Dict[str, Any]) -> bool:
        entry["status"] = "training"
        entry["current_training_episode"] = 0
        if total_training_episodes is not None:
            entry["total_training_episodes"] = int(total_training_episodes)
        return True

    _update_current_experiment(_updater)


def increment_training_episode() -> None:
    def _updater(entry: Dict[str, Any]) -> bool:
        if entry.get("status") != "training":
            return False
        current = _default_zero(entry.get("current_training_episode")) + 1
        entry["current_training_episode"] = current
        return True

    _update_current_experiment(_updater)


def set_evaluation_status(total_episodes: Optional[int] = None) -> None:
    def _updater(entry: Dict[str, Any]) -> bool:
        entry["status"] = "evaluation"
        entry["current_evaluation_episode"] = 0
        if total_episodes is not None:
            entry["total_evaluation_episodes"] = int(total_episodes)
        return True

    _update_current_experiment(_updater)


def increment_evaluation_episode() -> None:
    def _updater(entry: Dict[str, Any]) -> bool:
        if entry.get("status") != "evaluation":
            return False
        current = _default_zero(entry.get("current_evaluation_episode")) + 1
        entry["current_evaluation_episode"] = current
        return True

    _update_current_experiment(_updater)


def calculate_total_training_episodes(
    training_timesteps: int, env_config_path: Optional[str]
) -> Optional[int]:
    try:
        timesteps = int(training_timesteps)
    except (TypeError, ValueError):
        return None

    if timesteps <= 0 or not env_config_path:
        return None

    try:
        config = parse_sinergym_environment_config(env_config_path)
    except Exception:
        return None

    episode = getattr(config, "episode", None)
    if not episode or episode.timesteps_per_hour is None or episode.period is None:
        return None

    period = episode.period
    if len(period) != 6:
        return None

    start_day, start_month, start_year, end_day, end_month, end_year = period

    try:
        start = date(start_year, start_month, start_day)
        end = date(end_year, end_month, end_day)
    except ValueError:
        return None

    days = (end - start).days
    if days <= 0:
        return None

    timesteps_per_episode = days * 24 * episode.timesteps_per_hour
    if timesteps_per_episode <= 0:
        return None

    total_episodes = math.ceil(timesteps / timesteps_per_episode)
    return max(total_episodes, 1)
