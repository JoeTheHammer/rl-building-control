from datetime import datetime

import gymnasium as gym
import numpy as np
import copy
import h5py

from wrappers.normalization_utils import denormalize_state, get_original_action


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
        self.denorm_state = denorm_state
        self.state_names = None
        self.action_names = None
        self.reset_recordings()

    def reset_recordings(self):
        """Reset all collected logs (states, actions, rewards)."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.state_names = None
        self.action_names = None

    def start_recording(self):
        """Begin logging states, actions, and rewards."""
        self.is_recording = True
        self.reset_recordings()

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
        return obs, reward, terminated, truncated, info


    def export_to_hdf5(self, file_path: str):
        """
        Dump the entire current recording to an HDF5 file.
        """
        if not self.rewards:
            print("No data recorded — nothing to export.")
            return

        actions_arr = _flatten(self.actions)
        states_arr = _flatten(self.states)
        rewards_arr = np.array(self.rewards)

        # Create or overwrite file
        with h5py.File(file_path, "w") as f:
            # Store main data arrays
            f.create_dataset("states", data=states_arr, compression="gzip")
            f.create_dataset("actions", data=actions_arr, compression="gzip")
            f.create_dataset("rewards", data=rewards_arr, compression="gzip")

            # Optional names
            if self.state_names:
                f.create_dataset("state_names", data=np.array(self.state_names, dtype=h5py.string_dtype()))
            if self.action_names:
                f.create_dataset("action_names", data=np.array(self.action_names, dtype=h5py.string_dtype()))

            # Metadata
            f.attrs["export_time"] = datetime.now().isoformat()
            f.attrs["denormalized"] = self.denorm_state
            f.attrs["num_steps"] = len(rewards_arr)

        print(f"Recording exported to {file_path}")