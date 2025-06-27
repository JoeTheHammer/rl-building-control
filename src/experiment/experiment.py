from typing import Any, List

from controllers.base_controller import IController
from custom_loggers.experiment_logger import logger
from environments.base_env import IEnvironment
from reporting.plotter import plot_timeseries
from wrappers.normalization_utils import denormalize_state


def print_results(rewards: List[float], actions: List[Any], states: List[Any]):
    plot_timeseries("Reward", rewards)


class Experiment:
    def __init__(
        self,
        name: str,
        env: IEnvironment,
        controller: IController,
        num_episodes: int = 1,
        denorm_state: bool = False,
    ):
        self.name = name
        self.env = env
        self.controller = controller
        self.num_episodes = num_episodes
        self.denorm_state = denorm_state

    def run(self) -> List[float]:
        """Run `num_episodes` in this environment and return a list of total episode_rewards."""

        logger.info(f"Experiment {self.name} started for {self.num_episodes} episodes.")
        episode_rewards = []
        total_rewards = []
        states = []
        actions = []

        for ep in range(1, self.num_episodes + 1):
            episode_reward = 0
            state, _ = self.env.reset()
            done = False

            while not done:
                action = self.controller.get_action(state)
                state, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                episode_reward += reward

                total_rewards.append(reward)
                # Append denormalized state if given in config, else original state.
                states.append(
                    state if not self.denorm_state else denormalize_state(state, self.env)
                )

                actions.append(action)

            logger.info(f"Episode {ep}/{self.num_episodes} finished — reward: {episode_reward}")
            episode_rewards.append(episode_reward)

        self.env.close()
        logger.info(f"Experiment {self.name} complete.")

        print_results(total_rewards, [], [])

        return episode_rewards
