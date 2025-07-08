from parser.config_parser import parse_experiment_list
from typing import Dict, List

import gymnasium as gym

from controllers.base_controller import IController, IControllerProvider
from custom_loggers.setup_logger import logger as setup_logger
from environments.base_env import IEnvironment
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment
from experiment.experiment_config import ExperimentConfig


class ExperimentManager:
    def __init__(self):
        self._env_providers: Dict[str, IEnvironmentProvider] = {}
        self._experiments: List[Experiment] = []
        self._controller_providers: Dict[str, IControllerProvider] = {}

    def setup_experiments(self, config_path: str):
        """
        Parses and initializes all experiments defined in the environment_config file.

        Args:
            config_path (str): Path to the YAML environment_config file containing experiment definitions.
        """
        experiment_configs = parse_experiment_list(config_path)
        for experiment_config in experiment_configs.experiments:
            setup_logger.info(f"Setting up experiment {experiment_config.name}")
            experiment = self._create_experiment(experiment_config)
            if experiment is None:
                setup_logger.warning(f"Experiment {experiment_config.name} could not be created.")
                continue
            self._register_experiment(experiment)

    def _create_experiment(self, experiment_config: ExperimentConfig) -> Experiment | None:
        env, env_provider = self._create_environment(experiment_config)

        if env is None:
            setup_logger.error(f"Failed to create environment {experiment_config.name}")
            return None

        setup_logger.info(f"Environment for engine {experiment_config.engine} created.")

        controller = self._create_controller(env, experiment_config, env_provider)
        if controller is None:
            setup_logger.error(f"Failed to create controller {experiment_config.controller}")
            return None

        setup_logger.info(f"Controller for algorithm {experiment_config.controller} created.")

        return Experiment(
            experiment_config.name,
            env,
            controller,
            denorm_state=experiment_config.reporting.denormalize_state,
            episodes=experiment_config.episodes,
            plots=experiment_config.reporting.plots,
            export=experiment_config.reporting.export,
        )

    def _create_environment(
        self, experiment_config: ExperimentConfig
    ) -> tuple[IEnvironment, IEnvironmentProvider] | None:
        env_provider = self._env_providers.get(experiment_config.engine)
        if env_provider is None:
            setup_logger.error(
                f"No environment provider registered for engine '{experiment_config.engine}'."
            )
            return None
        return env_provider.create_environment(experiment_config.environment_config), env_provider

    def _create_controller(
        self, env: gym.Env, experiment_config: ExperimentConfig, env_provider: IEnvironmentProvider
    ) -> IController | None:
        controller_provider = self._controller_providers.get(experiment_config.controller)
        if controller_provider is None:
            setup_logger.error(
                f"No controller provider registered for algorithm '{experiment_config.controller}'."
            )
            return None

        return controller_provider.create_controller(
            env,
            experiment_config.controller_config,
            env_provider,
            experiment_config.environment_config,
        )

    def _register_experiment(self, experiment: Experiment) -> None:
        """Registers an experiment by adding it to the experiments list."""
        self._experiments.append(experiment)

    def register_controller_provider(self, controller: str, provider: IControllerProvider) -> None:
        """Register a controller provider for a specific algorithm."""
        self._controller_providers[controller] = provider

    def register_environment_provider(self, engine: str, provider: IEnvironmentProvider):
        """Register an environment provider for a specific engine."""
        self._env_providers[engine] = provider

    def run_all(self):
        """Run all experiments that are registered."""
        for experiment in self._experiments:
            # TODO: Add exception handling later
            experiment.run()
