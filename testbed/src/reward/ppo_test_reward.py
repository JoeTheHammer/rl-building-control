import numpy as np
from sinergym import BaseReward


class SimpleTemperatureComfortReward(BaseReward):
    """
    Calculates a reward based ONLY on how close the temperature is to the target.
    Designed for simplicity and efficiency.
    """

    def __init__(
        self,
        target_temp=23.0,
        sigma=1.0,  # Controls sharpness of the reward peak (how forgiving it is)
        min_reward=-10.0,  # Optional: a slightly less harsh minimum reward if needed
    ):
        super().__init__()
        self.target_temp = target_temp
        self.sigma = sigma
        self.min_reward = min_reward  # Still useful to prevent single-step catastrophes

    def __call__(self, obs_dict):
        default_temp = self.target_temp

        # Get current observed temperatures for both zones
        temp_101 = obs_dict.get("air_temp_101", default_temp)
        temp_104 = obs_dict.get("air_temp_104", default_temp)

        comfort_score_101 = np.exp(-((temp_101 - self.target_temp) ** 2) / (2 * self.sigma**2))
        comfort_score_104 = np.exp(-((temp_104 - self.target_temp) ** 2) / (2 * self.sigma**2))

        combined_comfort_score = min(comfort_score_101, comfort_score_104)
        final_reward = 2 * combined_comfort_score - 1

        info = {
            "reward": final_reward,
            "comfort_score_101": comfort_score_101,
            "comfort_score_104": comfort_score_104,
            "temp_101": temp_101,
            "temp_104": temp_104,
            "setpoint_101": obs_dict.get("setpoint_temp", default_temp),
            "setpoint_104": obs_dict.get("setpoint_temp_2", default_temp),
        }
        return final_reward, info
