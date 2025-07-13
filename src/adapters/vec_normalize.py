from typing import Type

import gymnasium as gym
import numpy as np
from stable_baselines3.common.on_policy_algorithm import OnPolicyAlgorithm
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from controllers.base_controller import IController
from wrappers.reporting_wrapper import ReportingWrapper


class VecNormalizeAdapter(gym.Wrapper, IController):
    """
    A generic adapter for any Stable Baselines3 on-policy algorithm (like PPO or A2C),
    with action logging on predict and on environment step.
    """

    def __init__(self, env: gym.Env, model_class: Type[OnPolicyAlgorithm], hyperparams: dict):
        # Wrap pure_env in ActionLoggingWrapper so scaled actions are logged on step()

        super().__init__(env)

        hyperparams["max_grad_norm"] = 0.5
        hyperparams["target_kl"] = 0.03

        self.reporting_env = ReportingWrapper(env, denorm_state=True)

        # CHANGED: The DummyVecEnv now gets the reporting_env instance
        self.vec_env = VecNormalize(DummyVecEnv([lambda: self.reporting_env]), norm_reward=False)

        self._model = model_class("MlpPolicy", self.vec_env, **hyperparams)

        self.action_space = self._model.action_space

        original_predict = self._model.predict

        def patched_predict(obs, *args, **kwargs):
            action, state = original_predict(obs, *args, **kwargs)
            return action, state

        self._model.predict = patched_predict

    def get_action(self, state: np.ndarray) -> np.ndarray:
        action, _ = self._model.predict(np.expand_dims(state, axis=0), deterministic=True)
        return action[0]

    def step(self, action: np.ndarray):
        obs, reward, done, info = self.vec_env.step(np.array([action]))

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
        return obs[0], {}

    def train(self, timesteps: int):
        self._model.learn(total_timesteps=timesteps)
