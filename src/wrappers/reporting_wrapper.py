import gymnasium as gym
import numpy as np

from reporting.plotter import plot_timeseries


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

    This wrapper collects observations (states), actions, and rewards
    during agent-environment interaction when recording is enabled.
    The user can start and end recording at any time by calling
    `start_recording()` and `end_recording()` respectively. Collected data
    can be visualized using the `create_plots()` method, which uses `plot_timeseries`.
    """

    def __init__(self, env):
        """
        Initialize the LoggingWrapper.

        Args:
            env (gym.Env): The environment to wrap.
        """
        super().__init__(env)
        self.is_recording = False
        self.states = []
        self.actions = []
        self.rewards = []
        self.reset_logs()

    def reset_logs(self):
        """
        Reset all collected logs (states, actions, rewards).
        """
        self.states = []
        self.actions = []
        self.rewards = []

    def start_recording(self):
        """
        Begin logging states, actions, and rewards.
        Resets any previously collected logs.
        """
        self.is_recording = True
        self.reset_logs()

    def end_recording(self):
        """
        Stop logging states, actions, and rewards.
        Does not erase collected data.
        """
        self.is_recording = False

    def step(self, action):
        """
        Step the environment with the given action and optionally log the result.

        Args:
            action: The action to take.

        Returns:
            obs: The next observation (state).
            reward: The reward from the environment.
            terminated: Whether the episode terminated.
            truncated: Whether the episode was truncated.
            info: Auxiliary information from the environment.
        """
        obs, reward, terminated, truncated, info = self.env.step(action)
        if self.is_recording:
            self.states.append(obs)
            self.actions.append(action)
            self.rewards.append(reward)
        return obs, reward, terminated, truncated, info

    def reset(self, **kwargs):
        """
        Reset the environment and optionally log the initial state.

        Returns:
            obs: The initial observation (state).
            info: Auxiliary information from the environment.
        """
        obs, info = self.env.reset(**kwargs)
        if self.is_recording:
            self.states.append(obs)
        return obs, info

    def create_plots(self, output_dir="./plots", file_format="png"):
        """
        Generate and save plots for the collected rewards, actions, and states using plot_timeseries.

        Args:
            output_dir (str): Directory to save the plot images.
            file_format (str): File format to save as (e.g. 'png', 'pdf', 'svg').
        """

        # Plot rewards
        plot_timeseries("reward", self.rewards, output_dir, file_format)

        # Plot actions
        actions_arr = _flatten(self.actions)
        if actions_arr.ndim == 1:
            plot_timeseries("action_0", actions_arr, output_dir, file_format)
        else:
            for i in range(actions_arr.shape[1]):
                plot_timeseries(f"action_{i}", actions_arr[:, i], output_dir, file_format)

        # Plot states
        states_arr = _flatten(self.states)
        if states_arr.ndim == 1:
            plot_timeseries("state_0", states_arr, output_dir, file_format)
        else:
            for i in range(states_arr.shape[1]):
                plot_timeseries(f"state_{i}", states_arr[:, i], output_dir, file_format)
