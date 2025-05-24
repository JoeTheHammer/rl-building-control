from typing import Any, Dict, List, Optional, Type

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
        # STEP FUNCTION TO TEST SETUP

        obs, reward, terminated, truncated, info = super().step(action)

        obs_dict = self.build_observation_dict(obs, action, info)

        reward, reward_info = self.reward_fn(obs_dict)
        return obs, reward, terminated, truncated, {**info, **reward_info}

    def build_observation_dict(
        self, obs: np.ndarray, action: np.ndarray, info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constructs a comprehensive observation dictionary containing:
        - Named state variables (from self.variables)
        - Meter readings (from self.meters)
        - Applied actuator values (from self.actuators and `action`)
        - Episode metadata (from `info`)

        The order of `obs` must match the order of keys in variables + meters.
        The order of `action` must match the order of keys in actuators.
        """
        ordered_state_keys = list(self.variables.keys()) + list(self.meters.keys())
        state_values = dict(zip(ordered_state_keys, obs))
        action_values = dict(zip(self.actuators.keys(), action))
        return {**state_values, **action_values, **info}
