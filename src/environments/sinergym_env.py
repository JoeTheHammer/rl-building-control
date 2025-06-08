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
        time_info: List[str] | None = None,
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

        state = self._add_time_information_to_state(obs, info)

        return state, reward, terminated, truncated, {**obs_dict, **reward_info}

    def _add_time_information_to_state(self, obs, info) -> np.ndarray:
        """
        Adds selected time-related features from the info dict to the observation array.
        Raises an error if a required key is missing.
        """
        state = list(obs)  # assuming obs is a NumPy array

        if self.time_info is not None:
            for time_key in self.time_info:
                if time_key not in info:
                    raise KeyError(f"[step] Time feature '{time_key}' not found in info dict.")
                state.append(info[time_key])
        return np.array(state, dtype=np.float32)


    def reset(self, **kwargs):
        """
        Overwrites the reset function and adds time information as well if needed.
        """
        obs, info = super().reset(**kwargs)
        state = self._add_time_information_to_state(obs, info)
        return state, info
