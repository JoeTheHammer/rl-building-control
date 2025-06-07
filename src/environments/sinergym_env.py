from typing import Any, Dict, List, Optional, Type

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
    ):

        self.variables = variables
        self.meters = meters
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
        return obs, reward, terminated, truncated, {**obs_dict, **reward_info}
