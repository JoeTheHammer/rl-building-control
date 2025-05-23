import numpy as np
from sinergym.utils.rewards import BaseReward


class MyReward(BaseReward):
    def __init__(self, target_temp=23.0, sigma=1.0, smooth_action_penalty=0.0):
        super().__init__()
        self.target_temp = target_temp
        self.sigma = sigma  # Controls sharpness of the reward peak
        self.prev_action = None  # Store last action for smoothness penalty
        self.smooth_action_penalty = smooth_action_penalty  # weight for penalizing large jumps

    def __call__(self, obs_dict):
        temp = obs_dict.get("air_temp_101", 0.0)
        action = obs_dict.get("action", None)  # You'll need to pass this from the environment
        deviation = abs(temp - self.target_temp)

        # Gaussian reward centered at 23°C
        comfort_score = np.exp(-((temp - self.target_temp) ** 2) / (2 * (self.sigma**2)))
        reward = 2.0 * comfort_score - 1.0  # Range: [-1, +1]

        # Add action penalty to push away from 18
        if action is not None:
            reward -= 0.02 * abs(action - self.target_temp)  # 👈

        # Optional: smoothness penalty
        if action is not None and self.prev_action is not None:
            reward -= self.smooth_action_penalty * abs(action - self.prev_action)

        self.prev_action = action

        return reward, {
            "temp": temp,
            "reward": reward,
            "deviation": deviation,
            "comfort_score": comfort_score,
        }
