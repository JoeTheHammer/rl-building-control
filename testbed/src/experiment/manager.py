from datetime import datetime, UTC
from typing import Dict

from controllers.base_controller import ControllerSetup, IControllerFactory
from custom_loggers.setup_logger import logger as setup_logger
from environments.base_factory import IEnvironmentFactory
from experiment.experiment import Experiment
from experiment.experiment_config import ExperimentConfig, ReportingConfig
from experiment.status import initialize_status, set_current_experiment
from reporting.context import collect_experiment_context
from reporting.hdf5_storage import ExperimentStorage, HDF5StorageManager
from parser.config_parser import parse_experiment_list


class ExperimentManager:
    def __init__(self, storage_path: str | None = None, flush_interval: int = 1024):
        self._env_factories: Dict[str, IEnvironmentFactory] = {}
        self._controller_factories: Dict[str, IControllerFactory] = {}
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        default_storage = f"data-{timestamp}.h5"
        self._storage_path = storage_path or str(default_storage)
        self._flush_interval = flush_interval
        self._storage_manager: HDF5StorageManager | None = None

    def run_experiments_from_config(self, config_path: str):
        """
        Parses, creates, trains, and runs all experiments from a config file sequentially.
        """
        experiment_configs = parse_experiment_list(config_path)
        payload = [
            {
                "id": index,
                "name": experiment_config.name,
                "total_evaluation_episodes": experiment_config.episodes,
            }
            for index, experiment_config in enumerate(experiment_configs.experiments, start=1)
        ]
        initialize_status(payload)

        self._storage_manager = HDF5StorageManager(self._storage_path)

        try:
            for index, experiment_config in enumerate(experiment_configs.experiments, start=1):

                setup_logger.info(f"Creating experiment: {experiment_config.name} ---")

                set_current_experiment(index)
                experiment_storage = self._storage_manager.create_experiment(
                    index,
                    experiment_config.name,
                    metadata={
                        "engine": experiment_config.engine,
                        "environment_config": experiment_config.environment_config,
                        "controller": experiment_config.controller,
                        "controller_config": experiment_config.controller_config,
                        "episodes": experiment_config.episodes,
                    },
                )

                context = collect_experiment_context(config_path, experiment_config)
                experiment_storage.store_context(context)
                self._storage_manager.flush()

                experiment = self._create_experiment(experiment_config, index, experiment_storage)

                if experiment is None:
                    set_current_experiment(None)
                    setup_logger.warning(
                        f"Skipping run for experiment {experiment_config.name} due to creation failure."
                    )
                    continue

                # ADDED: Run the experiment immediately after it's created and trained.
                setup_logger.info(f"Running evaluation for experiment {experiment.name}")
                set_current_experiment(index)
                experiment.run()
                set_current_experiment(None)
                setup_logger.info(f"--- Finished experiment: {experiment.name} ---")
        finally:
            if self._storage_manager:
                self._storage_manager.close()
                self._storage_manager = None

    def _create_experiment(
        self,
        experiment_config: ExperimentConfig,
        experiment_id: int,
        experiment_storage: ExperimentStorage,
    ) -> Experiment | None:
        # This method's internal logic remains the same
        env_factory = self._create_environment_factory(experiment_config)
        if env_factory is None:
            setup_logger.error(f"Failed to create environment {experiment_config.name}")
            return None
        setup_logger.info(f"Environment for engine {experiment_config.engine} created.")

        controller_setup = self._create_controller(
            experiment_config, env_factory, experiment_id, experiment_storage
        )
        if controller_setup is None:
            setup_logger.error(f"Failed to create controller {experiment_config.controller}")
            return None
        setup_logger.info(f"Controller for algorithm {experiment_config.controller} created.")

        reporting = experiment_config.reporting or ReportingConfig()

        return Experiment(
            experiment_config.name,
            controller_setup.environment,
            controller_setup.controller,
            experiment_id=experiment_id,
            experiment_storage=experiment_storage,
            denorm_state=reporting.denormalize_state,
            episodes=experiment_config.episodes,
            flush_interval=self._flush_interval,
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
        self,
        experiment_config: ExperimentConfig,
        env_factory: IEnvironmentFactory,
        experiment_id: int,
        experiment_storage: ExperimentStorage,
    ) -> ControllerSetup | None:
        controller_factory = self._controller_factories.get(experiment_config.controller)
        if controller_factory is None:
            setup_logger.error(
                f"No controller factory registered for algorithm '{experiment_config.controller}'."
            )
            return None

        controller_factory.set_env_factory(env_factory)
        controller_factory.set_config_path(experiment_config.controller_config)
        controller_factory.set_experiment_storage(experiment_storage, self._flush_interval)

        set_current_experiment(experiment_id)
        return controller_factory.create_controller_setup()

    def register_controller_factory(self, controller: str, factory: IControllerFactory) -> None:
        self._controller_factories[controller] = factory

    def register_environment_factory(self, engine: str, factory: IEnvironmentFactory):
        self._env_factories[engine] = factory
