from typing import Any, Dict, Optional, Type

import numpy as np
from gymnasium.spaces import Box
from sinergym import BaseReward
from sinergym.envs import EplusEnv

from environments.base_env import IEnvironment


class SinergymEnvironment(EplusEnv, IEnvironment):
    def __init__(
        self,
        building_model_path: str,
        weather_data_path: str,
        variables: dict[str, tuple[str, str]],
        meters: dict[str, str],
        actuators: dict[str, tuple[str, str, str]],
        reward_function_cls: Type[BaseReward],
        reward_kwargs: Optional[Dict[str, Any]] = None,
        action_space: Box = Box(low=0, high=0, shape=(0,), dtype=np.float32),
    ):
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
        # STEP FUNCTION TO TEST SETUP

        # Correct shape of action
        if isinstance(action, (list, np.ndarray)):
            action = np.array(action, dtype=np.float32)
        else:
            action = np.array([action], dtype=np.float32)

        obs, reward, terminated, truncated, info = super().step(action)

        obs_dict = info.copy()
        # TODO: Extract information for reward based on reward config TBD ...
        obs_dict["air_temp_101"] = obs[0]
        obs_dict["action"] = action
        reward, reward_info = self.reward_fn(obs_dict)
        return obs, reward, terminated, truncated, {**info, **reward_info}
