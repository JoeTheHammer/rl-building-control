from pathlib import Path

import gymnasium as gym
import numpy as np
import pandas as pd

from reporting.plotter import plot_timeseries
from wrappers.normalization_utils import denormalize_state


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
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._maybe_extract_names(info, obs=obs, action=action)
        if self.is_recording:
            self.states.append(obs if not self.denorm_state else denormalize_state(obs, self.env))
            self.actions.append(action)
            self.rewards.append(reward)
        return obs, reward, terminated, truncated, info

    def create_plots(self, output_dir="./plots", file_format="png"):
        """Generate and save plots for the collected rewards, actions, and states."""
        if len(self.rewards) > 0:
            plot_timeseries("reward", self.rewards, output_dir, file_format)

        actions_arr = _flatten(self.actions)
        states_arr = _flatten(self.states)

        action_dir = output_dir + "/actions"
        state_dir = output_dir + "/states"

        # Actions plotting
        if (
            self.action_names is not None
            and actions_arr.ndim == 2
            and len(self.action_names) == actions_arr.shape[1]
        ):
            for i, name in enumerate(self.action_names):
                plot_timeseries(str(name), actions_arr[:, i], action_dir, file_format)
        elif (
            actions_arr.ndim == 1 and self.action_names is not None and len(self.action_names) == 1
        ):
            plot_timeseries(str(self.action_names[0]), actions_arr, action_dir, file_format)
        else:
            if actions_arr.ndim == 1:
                plot_timeseries("action_0", actions_arr, action_dir, file_format)
            elif actions_arr.ndim == 2:
                for i in range(actions_arr.shape[1]):
                    plot_timeseries(f"action_{i}", actions_arr[:, i], action_dir, file_format)

        # States plotting
        if (
            self.state_names is not None
            and states_arr.ndim == 2
            and len(self.state_names) == states_arr.shape[1]
        ):
            for i, name in enumerate(self.state_names):
                plot_timeseries(str(name), states_arr[:, i], state_dir, file_format)
        elif states_arr.ndim == 1 and self.state_names is not None and len(self.state_names) == 1:
            plot_timeseries(str(self.state_names[0]), states_arr, state_dir, file_format)
        else:
            if states_arr.ndim == 1:
                plot_timeseries("state_0", states_arr, state_dir, file_format)
            elif states_arr.ndim == 2:
                for i in range(states_arr.shape[1]):
                    plot_timeseries(f"state_{i}", states_arr[:, i], state_dir, file_format)

    def export_to_csv(self, output_dir="./export"):
        """
        Export the collected rewards, actions, and states to separate CSV files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export Rewards
        if self.rewards:
            pd.DataFrame({"reward": self.rewards}).to_csv(output_path / "rewards.csv", index=False)

        # Flatten collected data
        actions_arr = _flatten(self.actions)
        states_arr = _flatten(self.states)

        # Export Actions
        if actions_arr.size > 0:
            num_actions = actions_arr.shape[1] if actions_arr.ndim > 1 else 1
            if self.action_names and len(self.action_names) == num_actions:
                action_headers = self.action_names
            else:
                action_headers = [f"action_{i}" for i in range(num_actions)]

            pd.DataFrame(actions_arr, columns=action_headers).to_csv(
                output_path / "actions.csv", index=False
            )

        # Export States (includes the initial state)
        if states_arr.size > 0:
            num_states = states_arr.shape[1] if states_arr.ndim > 1 else 1
            if self.state_names and len(self.state_names) == num_states:
                state_headers = self.state_names
            else:
                state_headers = [f"state_{i}" for i in range(num_states)]

            pd.DataFrame(states_arr, columns=state_headers).to_csv(
                output_path / "states.csv", index=False
            )
