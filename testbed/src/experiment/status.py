from __future__ import annotations

import math
import os
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

import yaml

from parser.config_parser import parse_sinergym_environment_config

_STATUS_LOCK = Lock()
_STATUS_PATH = Path(os.getenv("EXPERIMENT_STATUS_FILE", Path.cwd() / "status.yaml"))


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


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def update_status(**updates: Any) -> None:
    cleaned = {key: value for key, value in updates.items() if value is not None}
    if not cleaned:
        return
    with _STATUS_LOCK:
        data = _load_status()
        data.update(cleaned)
        _write_status(data)


def set_hyperparameter_tuning_status() -> None:
    update_status(status="hyperparameter_tuning")


def set_training_status(total_training_episodes: Optional[int] = None) -> None:
    updates: Dict[str, Any] = {
        "status": "training",
        "current_training_episode": 0,
    }
    if total_training_episodes is not None:
        updates["total_training_episodes"] = int(total_training_episodes)
    update_status(**updates)


def increment_training_episode() -> None:
    with _STATUS_LOCK:
        data = _load_status()
        if data.get("status") != "training":
            return
        current = _coerce_int(data.get("current_training_episode")) + 1
        data["current_training_episode"] = current
        _write_status(data)


def set_evaluation_status(total_episodes: Optional[int] = None) -> None:
    updates: Dict[str, Any] = {
        "status": "evaluation",
        "current_evaluation_episode": 0,
    }
    if total_episodes is not None:
        updates["total_evaluation_episodes"] = int(total_episodes)
    update_status(**updates)


def increment_evaluation_episode() -> None:
    with _STATUS_LOCK:
        data = _load_status()
        if data.get("status") != "evaluation":
            return
        current = _coerce_int(data.get("current_evaluation_episode")) + 1
        data["current_evaluation_episode"] = current
        _write_status(data)


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
