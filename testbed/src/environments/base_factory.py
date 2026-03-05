from abc import ABC, abstractmethod

import gymnasium as gym


class EnvironmentFactory(ABC):
    """
    Abstract factory interface for creating experiment environments.

    Concrete factories are responsible for interpreting the given configuration
    file (typically a YAML path) and returning a fully constructed environment
    instance ready for use.
    """

    def __init__(self):
        self.config_path = ""
        self.seed: int | None = None

    def set_config_path(self, config_path: str):
        self.config_path = config_path

    def set_seed(self, seed: int | None):
        self.seed = seed

    @abstractmethod
    def create_environment(self) -> gym.Env:
        """
        Create and return an environment instance based on the provided configuration file.

        Returns:
            gym.Env: A fully constructed experiment environment instance.
        """
        pass
