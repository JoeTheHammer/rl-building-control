from datetime import datetime
from typing import Dict, Optional

import gymnasium as gym
import numpy as np
import copy
import h5py

from wrappers.normalization_utils import denormalize_state, get_original_action
from reporting.hdf5_storage import BaseStorageHandler, EvaluationStorageHandler


def _flatten(values):
    """
    Converts list of values to a numpy array.
    For objects that are arrays/lists, ensures correct stacking.
    """
    arr = np.array(values)
    if arr.dtype == object:
        arr = np.stack([np.asarray(v).flatten() for v in values])
    return arr.squeeze()


class ReportingWrapper(gym.Wrapper):
    """
    A Gymnasium wrapper that adds logging and visualization capabilities.
    """

    def __init__(self, env, denorm_state=False):
        super().__init__(env)
        self.is_recording = False
        self.states = []
        self.actions = []
        self.rewards = []
        self.non_state_metrics = []
        self.denorm_state = denorm_state
        self.state_names = None
        self.action_names = None
        self.non_state_metric_names = None
        self.storage_handler: Optional[BaseStorageHandler] = None
        self.flush_interval: int = 0
        self._state_names_sent = False
        self._action_names_sent = False
        self._non_state_names_sent = False
        self.reset_recordings()

    def configure_storage(
        self, handler: BaseStorageHandler, flush_interval: int = 1024
    ) -> None:
        self.storage_handler = handler
        self.flush_interval = max(1, flush_interval)
        handler.set_metadata({"denormalized": self.denorm_state})
        self._state_names_sent = False
        self._action_names_sent = False
        self._non_state_names_sent = False

    def begin_episode(self, episode_index: int, metadata: Optional[Dict[str, object]] = None):
        if isinstance(self.storage_handler, EvaluationStorageHandler):
            self.storage_handler.start_episode(episode_index, metadata)
        self.reset_recordings(keep_names=True)

    def finalize_episode(self, metadata: Optional[Dict[str, object]] = None):
        if not self.is_recording:
            return
        self._flush_buffer(force=True, keep_last_state=False)
        if isinstance(self.storage_handler, EvaluationStorageHandler):
            self.storage_handler.finalize_episode(metadata)
        self.reset_recordings(keep_names=True)

    def reset_recordings(self, keep_names: bool = False):
        """Reset all collected logs (states, actions, rewards)."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.non_state_metrics = []
        if not keep_names:
            self.state_names = None
            self.action_names = None
            self.non_state_metric_names = None
            self._state_names_sent = False
            self._action_names_sent = False
            self._non_state_names_sent = False

    def start_recording(self):
        """Begin logging states, actions, and rewards."""
        self.is_recording = True
        self.reset_recordings()
        if self.storage_handler:
            self.storage_handler.on_start()

    def end_recording(self):
        """Stop logging states, actions, and rewards."""
        self.is_recording = False

    def _maybe_extract_names(self, info, obs=None, action=None):
        """
        Extract state and action variable names from the info dict, if available.
        If dimensions don't match the latest obs/action, the names are ignored.
        """
        # Extract state names if present and not already set
        keys = info.get("state_keys", None)
        if self.state_names is None and isinstance(keys, (list, tuple)):
            self.state_names = list(keys)
        # Extract action names if present and not already set
        keys = info.get("action_keys", None)
        if self.action_names is None and isinstance(keys, (list, tuple)):
            self.action_names = list(keys)
        metric_keys = info.get("non_state_metric_keys", None)
        if self.non_state_metric_names is None and isinstance(metric_keys, (list, tuple)):
            self.non_state_metric_names = list(metric_keys)
        # Optionally, fallback for state/action length mismatch
        if obs is not None and self.state_names is not None:
            # If obs is 1D, treat as single variable
            if isinstance(obs, np.ndarray):
                obs_dim = obs.shape[-1] if obs.ndim > 0 else 1
                if len(self.state_names) != obs_dim:
                    self.state_names = None
        if action is not None and self.action_names is not None:
            if isinstance(action, np.ndarray):
                act_dim = action.shape[-1] if action.ndim > 0 else 1
                if len(self.action_names) != act_dim:
                    self.action_names = None

        self._update_storage_names()

    def reset(self, **kwargs):
        """
        Reset the environment and optionally log the initial state.
        """
        obs, info = self.env.reset(**kwargs)
        self._maybe_extract_names(info, obs=obs)
        if self.is_recording:
            self.states.append(obs if not self.denorm_state else denormalize_state(obs, self.env))
        return obs, info

    def step(self, action):
        """
        Step the environment with the given action and optionally log the result.
        """
        action_copy = copy.copy(action)
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._maybe_extract_names(info, obs=obs, action=action)
        if self.is_recording:
            self.states.append(obs if not self.denorm_state else denormalize_state(obs, self.env))
            self.actions.append(get_original_action(action_copy, self.env))
            self.rewards.append(reward)
            metrics = info.get("non_state_metrics")
            if metrics is not None:
                if isinstance(metrics, dict):
                    metric_names = self.non_state_metric_names or list(metrics.keys())
                    self.non_state_metrics.append(
                        [float(metrics.get(name, float("nan"))) for name in metric_names]
                    )
                else:
                    self.non_state_metrics.append(list(np.asarray(metrics).flatten()))
            self._maybe_flush()
        return obs, reward, terminated, truncated, info


    def _update_storage_names(self):
        if not self.storage_handler:
            return
        if self.state_names and not self._state_names_sent:
            self.storage_handler.set_state_names(self.state_names)
            self._state_names_sent = True
        if self.action_names and not self._action_names_sent:
            self.storage_handler.set_action_names(self.action_names)
            self._action_names_sent = True
        if self.non_state_metric_names and not self._non_state_names_sent:
            self.storage_handler.set_non_state_metric_names(self.non_state_metric_names)
            self._non_state_names_sent = True

    def _maybe_flush(self):
        if not self.storage_handler or not self.flush_interval:
            return
        if len(self.rewards) >= self.flush_interval:
            self._flush_buffer()

    def _flush_buffer(self, force: bool = False, keep_last_state: bool = True):
        if not self.storage_handler or not self.rewards:
            return
        if not force and len(self.rewards) < self.flush_interval:
            return

        self._update_storage_names()

        states_arr = _flatten(self.states)
        actions_arr = _flatten(self.actions) if self.actions else np.empty((0,))
        rewards_arr = np.array(self.rewards)
        metrics_arr = (
            _flatten(self.non_state_metrics)
            if self.non_state_metrics
            else np.empty((0,))
        )

        if rewards_arr.size == 0:
            return

        if keep_last_state and len(states_arr) > 1:
            states_to_store = states_arr[:-1]
        else:
            states_to_store = states_arr

        if len(states_to_store) == 0:
            return

        self.storage_handler.record_chunk(
            states_to_store,
            actions_arr,
            rewards_arr,
            metrics_arr,
        )

        if keep_last_state and len(states_arr) > 0:
            last_state = states_arr[-1]
            self.states = [last_state]
        else:
            self.states = []
        self.actions = []
        self.rewards = []
        self.non_state_metrics = []

    def export_to_hdf5(self, file_path: str | None = None):
        """
        Dump the entire current recording to an HDF5 file.
        """
        if self.storage_handler:
            self._flush_buffer(force=True, keep_last_state=False)
            self.storage_handler.finalize()
            return

        if not self.rewards:
            print("No data recorded — nothing to export.")
            return

        actions_arr = _flatten(self.actions)
        states_arr = _flatten(self.states)
        rewards_arr = np.array(self.rewards)
        metrics_arr = _flatten(self.non_state_metrics)

        if not file_path:
            raise ValueError("A file path must be provided when no storage handler is configured.")

        # Create or overwrite file
        with h5py.File(file_path, "w") as f:
            # Store main data arrays
            f.create_dataset("states", data=states_arr, compression="gzip")
            f.create_dataset("actions", data=actions_arr, compression="gzip")
            f.create_dataset("rewards", data=rewards_arr, compression="gzip")
            if metrics_arr.size:
                f.create_dataset("non_state_metrics", data=metrics_arr, compression="gzip")

            # Optional names
            if self.state_names:
                f.create_dataset("state_names", data=np.array(self.state_names, dtype=h5py.string_dtype()))
            if self.action_names:
                f.create_dataset("action_names", data=np.array(self.action_names, dtype=h5py.string_dtype()))
            if self.non_state_metric_names:
                f.create_dataset(
                    "non_state_metric_names",
                    data=np.array(self.non_state_metric_names, dtype=h5py.string_dtype()),
                )

            # Metadata
            f.attrs["export_time"] = datetime.now().isoformat()
            f.attrs["denormalized"] = self.denorm_state
            f.attrs["num_steps"] = len(rewards_arr)

        print(f"Recording exported to {file_path}")