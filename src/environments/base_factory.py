from abc import ABC, abstractmethod

import gymnasium as gym

class IEnvironmentFactory(ABC):
    """
    Abstract factory interface for creating experiment environments.

    Concrete factories are responsible for interpreting the given configuration
    file (typically a YAML path) and returning a fully constructed environment
    instance ready for use.
    """

    def __init__(self):
        self.config_path = ""

    def set_config_path(self, config_path: str):
        self.config_path = config_path


    @abstractmethod
    def create_environment(self) -> gym.Env:
        """
        Create and return an environment instance based on the provided configuration file.

        Returns:
            IEnvironment: A fully constructed experiment environment instance.
        """
        pass
