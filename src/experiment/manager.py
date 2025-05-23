from parser.config_parser import parse_experiment_list
from typing import Dict, List

from custom_loggers.setup_logger import logger as setup_logger
from environments.base_provider import EnvironmentProvider
from experiment.experiment import Experiment
from experiment.experiment_config import ExperimentConfig


class ExperimentManager:
    def __init__(self):
        self._providers: Dict[str, EnvironmentProvider] = {}
        self._experiments: List[Experiment] = []

    def setup_experiments(self, config_path: str):
        """
        Parses and initializes all experiments defined in the environment_config file.

        Args:
            config_path (str): Path to the YAML environment_config file containing experiment definitions.
        """
        experiment_configs = parse_experiment_list(config_path)
        for config_path in experiment_configs.experiments:
            setup_logger.info(f"Setting up experiment {config_path.name}")
            try:
                experiment = self._create_experiment(config_path)
                if experiment is None:
                    setup_logger.warning(f"Experiment {config_path.name} could not be created.")
                    continue
                self._register_experiment(experiment)
            except Exception as e:
                setup_logger.error(f"Failed to create experiment {config_path.name}: {e}")

    def _create_experiment(self, experiment_config: ExperimentConfig) -> Experiment | None:
        # TODO: Think about which attributes experiment needs, one is environment that must be provided by provider
        env_provider = self._providers.get(experiment_config.engine)
        if env_provider is None:
            setup_logger.error(
                f"No environment provider registered for engine '{experiment_config.engine}'."
            )
            return None
        env = env_provider.create_environment(experiment_config.environment_config)
        return Experiment(experiment_config.name, env)

    def _register_experiment(self, experiment: Experiment) -> None:
        """Registers an experiment by adding it to the experiments list."""
        self._experiments.append(experiment)

    def register_environment_provider(self, engine: str, provider: EnvironmentProvider):
        """Register an environment provider for a specific engine."""
        self._providers[engine] = provider

    def run_all(self):
        """Run all experiments that are registered."""
        for experiment in self._experiments:
            # TODO: Add exception handling later
            experiment.run()
