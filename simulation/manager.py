from typing import Dict, List

from environments.base_provider import EnvironmentProvider
from simulation.experiment import Experiment, ExperimentConfig


class ExperimentManager:
    def __init__(self):
        self._providers: Dict[str, EnvironmentProvider] = {}
        self._experiments: List[Experiment] = []
        
    def register_environment_provider(self, engine: str, provider: EnvironmentProvider):
        """Register an environment provider for a specific engine."""
        self._providers[engine] = provider

    def register_experiment(self, experiment: ExperimentConfig):
        #TODO: Build experiment from config, choose right Environment provider, use to build environment
        pass

    def run_all(self):
        """Run all experiments that are registered."""
        pass


