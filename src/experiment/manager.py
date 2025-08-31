from parser.config_parser import parse_experiment_list
from typing import Dict

from controllers.base_controller import ControllerSetup, IControllerFactory
from custom_loggers.setup_logger import logger as setup_logger
from environments.base_factory import IEnvironmentFactory
from experiment.experiment import Experiment
from experiment.experiment_config import ExperimentConfig


class ExperimentManager:
    def __init__(self):
        self._env_factories: Dict[str, IEnvironmentFactory] = {}
        self._controller_factories: Dict[str, IControllerFactory] = {}

    def run_experiments_from_config(self, config_path: str):
        """
        Parses, creates, trains, and runs all experiments from a config file sequentially.
        """
        experiment_configs = parse_experiment_list(config_path)
        for experiment_config in experiment_configs.experiments:

            setup_logger.info(f"Creating experiment: {experiment_config.name} ---")

            experiment = self._create_experiment(experiment_config)

            if experiment is None:
                setup_logger.warning(
                    f"Skipping run for experiment {experiment_config.name} due to creation failure."
                )
                continue

            # ADDED: Run the experiment immediately after it's created and trained.
            setup_logger.info(f"Running evaluation for experiment {experiment.name}")
            experiment.run()
            setup_logger.info(f"--- Finished experiment: {experiment.name} ---")

    def _create_experiment(self, experiment_config: ExperimentConfig) -> Experiment | None:
        # This method's internal logic remains the same
        env_factory = self._create_environment_factory(experiment_config)
        if env_factory is None:
            setup_logger.error(f"Failed to create environment {experiment_config.name}")
            return None
        setup_logger.info(f"Environment for engine {experiment_config.engine} created.")

        controller_setup = self._create_controller(experiment_config, env_factory)
        if controller_setup is None:
            setup_logger.error(f"Failed to create controller {experiment_config.controller}")
            return None
        setup_logger.info(f"Controller for algorithm {experiment_config.controller} created.")

        return Experiment(
            experiment_config.name,
            controller_setup.environment,
            controller_setup.controller,
            denorm_state=experiment_config.reporting.denormalize_state,
            episodes=experiment_config.episodes,
            plots=experiment_config.reporting.plots,
            export=experiment_config.reporting.export,
        )

    def _create_environment_factory(
        self, experiment_config: ExperimentConfig
    ) -> IEnvironmentFactory | None:
        env_factory = self._env_factories.get(experiment_config.engine)
        env_factory.set_config_path(experiment_config.environment_config)
        if env_factory is None:
            setup_logger.error(
                f"No environment factory registered for engine '{experiment_config.engine}'."
            )
            return None
        return env_factory

    def _create_controller(
        self, experiment_config: ExperimentConfig, env_factory: IEnvironmentFactory
    ) -> ControllerSetup | None:
        controller_factory = self._controller_factories.get(experiment_config.controller)
        if controller_factory is None:
            setup_logger.error(
                f"No controller factory registered for algorithm '{experiment_config.controller}'."
            )
            return None
        return controller_factory.create_controller_setup(
            experiment_config.controller_config,
            env_factory,
        )

    def register_controller_factory(self, controller: str, factory: IControllerFactory) -> None:
        self._controller_factories[controller] = factory

    def register_environment_factory(self, engine: str, factory: IEnvironmentFactory):
        self._env_factories[engine] = factory
