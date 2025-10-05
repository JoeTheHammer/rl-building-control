from typing import List

import gymnasium as gym

from controllers.base_controller import IController
from custom_loggers.experiment_logger import logger
from reporting.hdf5_storage import ExperimentStorage
from wrappers.reporting_wrapper import ReportingWrapper

from experiment.status import (
    increment_evaluation_episode,
    set_current_experiment,
    set_evaluation_status,
)


class Experiment:
    def __init__(
        self,
        name: str,
        env: gym.Env,
        controller: IController,
        experiment_id: int,
        experiment_storage: ExperimentStorage | None = None,
        episodes: int = 1,
        denorm_state: bool = False,
        plots: bool = False,
        export: bool = False,
        status_tracking: bool = True,
        flush_interval: int = 1024,
    ):
        self.name = name
        self.env = env
        self.controller = controller
        self.experiment_id = experiment_id
        self.episodes = episodes
        self.denorm_state = denorm_state
        self.plots = plots
        self.export = export
        self.report = self.plots or self.export
        self.status_tracking = status_tracking
        self.experiment_storage = experiment_storage
        self.flush_interval = flush_interval

    def run(self) -> List[float]:
        """Run `num_episodes` in this environment and return a list of total episode_rewards."""

        logger.info(f"Experiment {self.name} started for {self.episodes} episodes.")
        if self.status_tracking:
            set_current_experiment(self.experiment_id)
            set_evaluation_status(self.episodes)
        episode_rewards = []
        total_rewards = []

        if self.report:
            self._setup_reporting()

        for ep in range(1, self.episodes + 1):

            if self.status_tracking:
                increment_evaluation_episode()

            if self.report and isinstance(self.env, ReportingWrapper):
                self.env.begin_episode(ep)

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
            if self.report and isinstance(self.env, ReportingWrapper):
                self.env.finalize_episode({"episode_reward": float(episode_reward)})
        if self.report:
            self._report()

        self.env.close()
        logger.info(f"Experiment {self.name} complete.")

        if self.experiment_storage:
            self.experiment_storage.update_metadata(
                total_evaluation_reward=float(sum(episode_rewards)),
                evaluation_episodes=self.episodes,
            )

        return episode_rewards

    def _setup_reporting(self):
        self.env = ReportingWrapper(self.env, denorm_state=self.denorm_state)
        if self.experiment_storage:
            evaluation_handler = self.experiment_storage.create_evaluation_handler()
            evaluation_handler.set_metadata(
                {
                    "phase": "evaluation",
                    "denormalized": self.denorm_state,
                }
            )
            self.env.configure_storage(evaluation_handler, flush_interval=self.flush_interval)
        self.env.start_recording()

    def _report(self):

        if not isinstance(self.env, ReportingWrapper):
            logger.warning(
                "Report method called, but environment is not a ReportingWrapper. Skipping report."
            )
            return

        self.env.end_recording()
        logger.info("Writing data to HDF5...")
        self.env.export_to_hdf5()
        self.env.reset_recordings()
