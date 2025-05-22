import numpy as np
from gym.spaces import Box
from sinergym.envs import EplusEnv

from environments.base_env import IEnvironment
from reward.reward import MyReward


class SinergymEnvironment(EplusEnv, IEnvironment):
    def __init__(
        self,
        building_model_path: str,
        weather_data_path: str,
        variables: dict[str, tuple[str, str]],
        meters: dict[str, str],
        actuators: dict[str, tuple[str, str, str]],
        action_space: Box = Box(low=0, high=0, shape=(0,), dtype=np.float32),
    ):
        super().__init__(
            building_file=building_model_path,
            weather_files=weather_data_path,
            variables=variables,
            meters=meters,
            actuators=actuators,
            action_space=action_space,
            reward=MyReward,
        )
