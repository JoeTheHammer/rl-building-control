from typing import Any, Dict, List, Optional, Type

import numpy as np
from gymnasium.spaces import Box
from sinergym import BaseReward
from sinergym.envs import EplusEnv

from environments.base_env import IEnvironment
from utils.observation import build_observation_dict


class SinergymEnvironment(EplusEnv, IEnvironment):
    def __init__(
        self,
        building_model_path: str,
        weather_data_path: str,
        variables: dict[str, tuple[str, str]],
        meters: dict[str, str],
        actuators: dict[str, tuple[str, str, str]],
        reward_variables: List[str],
        reward_function_cls: Type[BaseReward],
        reward_kwargs: Optional[Dict[str, Any]] = None,
        action_space: Box = Box(low=0, high=0, shape=(0,), dtype=np.float32),
    ):

        self.variables = variables
        self.meters = meters
        self.reward_variables = reward_variables

        super().__init__(
            building_file=building_model_path,
            weather_files=weather_data_path,
            variables=variables,
            meters=meters,
            actuators=actuators,
            action_space=action_space,
            reward=reward_function_cls,
            reward_kwargs=reward_kwargs,
        )

    def step(self, action):

        obs, reward, terminated, truncated, info = super().step(action)

        obs_dict = build_observation_dict(
            obs=obs,
            action=action,
            info=info,
            variables=self.variables,
            meters=self.meters,
            actuators=self.actuators,
        )

        reward, reward_info = self.reward_fn(obs_dict)
        return obs, reward, terminated, truncated, {**info, **reward_info}
