from typing import Type

import gymnasium as gym
import numpy as np
from sinergym.utils.wrappers import NormalizeAction
from stable_baselines3.common.on_policy_algorithm import OnPolicyAlgorithm
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from controllers.base_controller import IController
from wrappers.reporting_wrapper import ReportingWrapper


class OnPolicyAdapter(gym.Wrapper, IController):
    """
    A generic adapter for any Stable Baselines3 on-policy algorithm (like PPO or A2C),
    with action logging on predict and on environment step.
    """

    def __init__(
        self,
        env: gym.Env,
        model_class: Type[OnPolicyAlgorithm],
        hyperparams: dict,
        normalize_reward: bool = False,
        report_denormalized_state: bool = False,
        policy: str = "MlpPolicy",
        normalize_action: bool = False,
    ):

        super().__init__(env)

        self.policy = policy
        self.lstm_states = None
        self.episode_starts = np.ones((1,), dtype=bool)

        self.env = ReportingWrapper(env, denorm_state=report_denormalized_state)

        if normalize_action:
            self.env = NormalizeAction(self.env)

        self.vec_env = VecNormalize(DummyVecEnv([lambda: self.env]), norm_reward=normalize_reward)

        self._model = model_class(policy, self.vec_env, **hyperparams)

        self.action_space = self._model.action_space

        original_predict = self._model.predict

        def patched_predict(obs, *args, **kwargs):
            action, state = original_predict(obs, *args, **kwargs)
            return action, state

        self._model.predict = patched_predict

    def get_action(self, state: np.ndarray) -> np.ndarray:
        if self.policy == "MlpLstmPolicy":
            action, lstm_states = self._model.predict(
                np.expand_dims(state, axis=0),
                state=self.lstm_states,
                episode_start=self.episode_starts,
                deterministic=True,
            )
            self.lstm_states = lstm_states
            return action[0]

        action, _ = self._model.predict(np.expand_dims(state, axis=0), deterministic=True)
        return action[0]

    def step(self, action: np.ndarray):
        obs, reward, done, info = self.vec_env.step(np.array([action]))

        self.episode_starts = done

        single_obs = obs[0]
        single_reward = reward[0]
        single_info = info[0]

        terminated = done[0] and "TimeLimit.truncated" not in single_info
        truncated = "TimeLimit.truncated" in single_info and single_info.get(
            "TimeLimit.truncated", False
        )

        return single_obs, single_reward, terminated, truncated, single_info

    def reset(self, **kwargs):
        obs = self.vec_env.reset()
        self.lstm_states = None
        return obs[0], {}

    def train(self, timesteps: int):
        # Set log_interval to 1 to increase support for tensor graph integration (more regular logs).
        self._model.learn(total_timesteps=timesteps, log_interval=1)
