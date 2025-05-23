import random

import numpy as np

from environments.base_env import IEnvironment


class Experiment:
    def __init__(self, name: str, env: IEnvironment):
        self.name = name
        self.env = env

    def run(self):

        # Random control to test setup
        obs, _ = self.env.reset()

        print(f"Observation: {obs}")
        done = False
        total_reward = 0
        actions = []

        while not done:
            action_value = random.uniform(18, 28)
            random_action = np.array([action_value], dtype=np.float32)

            obs, reward, terminated, truncated, info = self.env.step(random_action)

            actions.append(random_action)
            done = terminated or truncated
            total_reward += reward

        self.env.close()
        print("Experiment Finished!")
