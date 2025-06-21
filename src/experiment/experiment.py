from typing import List

from controllers.base_controller import IController
from custom_loggers.experiment_logger import logger
from environments.base_env import IEnvironment


class Experiment:
    def __init__(
        self,
        name: str,
        env: IEnvironment,
        controller: IController,
        num_episodes: int = 2,
    ):
        self.name = name
        self.env = env
        self.controller = controller
        self.num_episodes = num_episodes

    def run(self) -> List[float]:
        """Run `num_episodes` in this environment and return a list of total rewards."""

        logger.info(f"Experiment {self.name} started for {self.num_episodes} episodes.")
        rewards = []
        for ep in range(1, self.num_episodes + 1):
            episode_reward = 0
            state, _ = self.env.reset()
            done = False

            while not done:
                action = self.controller.get_action(state)
                state, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                episode_reward += reward

            logger.info(f"Episode {ep}/{self.num_episodes} finished — reward: {episode_reward}")
            rewards.append(episode_reward)

        self.env.close()
        logger.info(f"Experiment {self.name} complete.")

        return rewards
