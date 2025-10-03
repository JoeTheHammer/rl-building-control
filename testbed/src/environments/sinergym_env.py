import math
from typing import Any, Dict, List, Optional, Type

import gymnasium as gym
import numpy as np
from sinergym import BaseReward
from sinergym.envs import EplusEnv

from spaces.custom_action_space import ActuatorActionSpace
from utils.observation import build_info_dict

from experiment.status import increment_training_episode


class SinergymEnvironment(EplusEnv):
    def __init__(
        self,
        building_model_path: str,
        weather_data_path: str,
        variables: dict[str, tuple[str, str]],
        meters: dict[str, str],
        actuators: dict[str, tuple[str, str, str]],
        reward_variables: List[str],
        reward_function_cls: Type[BaseReward],
        action_space: ActuatorActionSpace,
        reward_kwargs: Optional[Dict[str, Any]] = None,
        time_info: dict[str, dict[str, bool]] | None = None,
        config_params: dict[str, Any] | None = None,
    ):

        self.variables = variables
        self.meters = meters
        self.time_info = time_info
        self.reward_variables = reward_variables
        self.custom_action_space = action_space
        self.discrete_mappings = self.custom_action_space.discrete_mappings
        self.expect_raw_actions = False
        self.continuous_action_space = False
        self.box_action_space = action_space.get_box_space()

        super().__init__(
            building_file=building_model_path,
            weather_files=weather_data_path,
            variables=variables,
            meters=meters,
            actuators=actuators,
            action_space=self.box_action_space,
            reward=reward_function_cls,
            reward_kwargs=reward_kwargs,
            config_params=config_params,
        )

    @property
    def observation_space(self):
        base_dim = len(self.variables) + len(self.meters)

        time_dim = 0
        if self.time_info is not None:
            for time_key, options in self.time_info.items():
                if options.get("cyclic", False):
                    time_dim += 2  # sin and cos
                else:
                    time_dim += 1  # scalar value

        total_dim = base_dim + time_dim

        return gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(total_dim,),
            dtype=np.float32,
        )

    @property
    def action_space(self):
        return self.custom_action_space.tuple_space

    def step(self, action):

        action = self.custom_action_space.to_eplus_action(action)

        # We ignore reward as we calculate it later in this method.
        obs, _, terminated, truncated, _ = super().step(action)
        state, time_info_dict = self._add_time_information_to_state(obs)

        info_dict = build_info_dict(
            obs=obs,
            action=action,
            time_info=time_info_dict,
            variables=self.variables,
            meters=self.meters,
            actuators=self.actuators,
        )

        # Communicate to reward function that actual reward should be calculated.
        reward, reward_info = self.reward_fn(info_dict)

        return state, reward, terminated, truncated, info_dict

    def reset(self, **kwargs):
        """
        Overwrites the reset function and adds time information as well if needed.
        """
        obs, info = super().reset(**kwargs)
        increment_training_episode()
        state, time_info_dict = self._add_time_information_to_state(obs)
        return state, {**info, **time_info_dict}

    def _add_time_information_to_state(
        self, obs: np.ndarray
    ) -> tuple[np.ndarray, Dict[str, float]]:
        """
        Appends time features from EnergyPlus API to the observation.
        Returns both the augmented observation and a dict of time values including sin/cos.
        """
        state = list(obs)
        time_info_dict = {}

        if self.time_info is not None:
            sim = self.energyplus_simulator
            state_obj = sim.energyplus_state
            api = sim.api.exchange

            for time_key, options in self.time_info.items():
                cyclic = options.get("cyclic", False)

                if time_key == "day_of_month":
                    value = api.day_of_month(state_obj)
                    max_val = 31
                elif time_key == "day_of_week":
                    value = api.day_of_week(state_obj)
                    max_val = 7
                elif time_key == "hour":
                    value = api.hour(state_obj)
                    max_val = 23
                elif time_key == "minutes":
                    value = api.minutes(state_obj)
                    max_val = 60
                elif time_key == "month":
                    value = api.month(state_obj)
                    max_val = 12
                else:
                    raise ValueError(f"Unsupported time key: {time_key}")

                if cyclic:
                    radians = 2 * math.pi * value / max_val
                    sin_val = math.sin(radians)
                    cos_val = math.cos(radians)
                    state.extend([sin_val, cos_val])
                    time_info_dict[f"{time_key}_sin"] = sin_val
                    time_info_dict[f"{time_key}_cos"] = cos_val
                else:
                    state.append(value)
                    time_info_dict[time_key] = value

        return np.array(state, dtype=np.float32), time_info_dict
