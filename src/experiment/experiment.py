from typing import List

from controllers.base_controller import IController
from custom_loggers.experiment_logger import logger
from environments.base_env import IEnvironment
from wrappers.reporting_wrapper import ReportingWrapper


class Experiment:
    def __init__(
        self,
        name: str,
        env: IEnvironment,
        controller: IController,
        episodes: int = 1,
        denorm_state: bool = False,
        plots: bool = False,
        export: bool = False,
    ):
        self.name = name
        self.env = env
        self.controller = controller
        self.episodes = episodes
        self.denorm_state = denorm_state
        self.plots = plots
        self.export = export
        self.report = self.plots or self.export

    def run(self) -> List[float]:
        """Run `num_episodes` in this environment and return a list of total episode_rewards."""

        logger.info(f"Experiment {self.name} started for {self.episodes} episodes.")
        episode_rewards = []
        total_rewards = []

        if self.report:
            self._setup_reporting()

        for ep in range(1, self.episodes + 1):
            episode_reward = 0
            state, _ = self.env.reset()
            done = False

            while not done:
                action = self.controller.get_action(state)
                state, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                episode_reward += reward

                total_rewards.append(reward)

            logger.info(f"Episode {ep}/{self.episodes} finished — reward: {episode_reward}")
            episode_rewards.append(episode_reward)
        if self.report:
            self._report()

        self.env.close()
        logger.info(f"Experiment {self.name} complete.")

        return episode_rewards

    def _setup_reporting(self):
        self.env = ReportingWrapper(self.env, denorm_state=self.denorm_state)
        self.env.start_recording()

    def _report(self):

        if not isinstance(self.env, ReportingWrapper):
            logger.warning(
                "Report method called, but environment is not a ReportingWrapper. Skipping report."
            )
            return

        self.env.end_recording()

        if self.plots:
            logger.info("Creating plots...")
            self.env.create_plots(output_dir=f"Experiment_{self.name}")
        if self.export:
            logger.info("Exporting data...")
            self.env.export_to_csv(output_dir=f"Experiment_{self.name}")
        self.env.reset_recordings()
