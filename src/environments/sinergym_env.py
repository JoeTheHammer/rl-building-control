import math
from typing import Any, Dict, List, Optional, Type

import gymnasium
import numpy as np
from sinergym import BaseReward
from sinergym.envs import EplusEnv

from environments.base_env import IEnvironment
from spaces.custom_action_space import ActuatorActionSpace
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
        action_space: ActuatorActionSpace,
        reward_kwargs: Optional[Dict[str, Any]] = None,
        time_info: dict[str, dict[str, bool]] | None = None,
    ):

        self.variables = variables
        self.meters = meters
        self.time_info = time_info
        self.reward_variables = reward_variables
        self.custom_action_space = action_space
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
        )

    @property
    def observation_space(self):
        if self.time_info is not None:
            return gymnasium.spaces.Box(
                -np.inf,
                np.inf,
                (len(self.variables) + len(self.meters) + len(self.time_info),),
                np.float32,
            )
        return self._observation_space

    @property
    def action_space(self):
        if self.continuous_action_space:
            return self.box_action_space
        return self.custom_action_space.tuple_space

    def step(self, action):

        # Convert action from controller to "real" action supported by energy plus. This is needed,
        # as the action of the controller might be an index in a discrete action space. This can be
        # overruled by the controller (needed for rule-based controller or if controller only support
        # continuous environment)
        if not self.expect_raw_actions and not self.continuous_action_space:
            action = self.custom_action_space.to_eplus_action(action)

        # We ignore reward as we calculate it later in this method.
        obs, _, terminated, truncated, info = super().step(action)

        obs_dict = build_observation_dict(
            obs=obs,
            action=action,
            info=info,
            variables=self.variables,
            meters=self.meters,
            actuators=self.actuators,
        )

        # Communicate to reward function that actual reward should be calculated.
        obs_dict["__compute_reward__"] = True
        reward, reward_info = self.reward_fn(obs_dict)

        state = self._add_time_information_to_state(obs)

        return state, reward, terminated, truncated, {**obs_dict, **reward_info}

    def _add_time_information_to_state(self, obs: np.ndarray) -> np.ndarray:
        """
        Appends time features from the EnergyPlus API to the observation.
        Applies cyclic encoding if specified in time_info.
        """
        state = list(obs)

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
                    value = api.day_of_week(state_obj)  # 1=Sunday, 2=Monday, ..., 7=Saturday
                    max_val = 7
                elif time_key == "hour":
                    value = api.hour(state_obj)
                    max_val = 23
                elif time_key == "minutes":
                    value = api.minutes(state_obj)
                    max_val = 59
                elif time_key == "month":
                    value = api.month(state_obj)
                    max_val = 12
                else:
                    raise ValueError(f"Unsupported time key: {time_key}")

                if cyclic:
                    radians = 2 * math.pi * value / max_val
                    state.append(math.sin(radians))
                    state.append(math.cos(radians))
                else:
                    state.append(value)

        return np.array(state, dtype=np.float32)

    def reset(self, **kwargs):
        """
        Overwrites the reset function and adds time information as well if needed.
        """
        obs, info = super().reset(**kwargs)
        state = self._add_time_information_to_state(obs)
        return state, info
