from abc import ABC, abstractmethod

import gymnasium as gym


class IEnvironmentProvider(ABC):
    """
    Abstract factory interface for creating experiment environments.

    Concrete providers are responsible for interpreting the given configuration
    file (typically a YAML path) and returning a fully constructed environment
    instance ready for use.
    """

    @abstractmethod
    def create_environment(self, config_path: str) -> gym.Env:
        """
        Create and return an environment instance based on the provided configuration file.

        Args:
            config_path (str): Path to the environment configuration file. The format
                               and structure of this file are specific to the provider.

        Returns:
            IEnvironment: A fully constructed experiment environment instance.
        """
        pass
