from abc import ABC, abstractmethod

from config.base_config import IEnvironmentConfig
from environments.base_env import IEnvironment


class EnvironmentProvider(ABC):
    """
    Abstract factory for creating simulation environments.
    Concrete providers must define how to construct an environment
    based on a given configuration.
    """

    def __init__(self, config: IEnvironmentConfig):
        """
        Initialize the provider with a given environment config.

        Args:
            config (IEnvironmentConfig): The environment configuration.
        """
        self._config = config

    @abstractmethod
    def create_environment(self) -> IEnvironment:
        """
        Create and return an environment instance using the configuration.

        Returns:
            IEnvironment: A concrete environment instance.
        """
        pass

    def get_config(self) -> IEnvironmentConfig:
        """
        Return the configuration associated with this provider.

        Returns:
            IEnvironmentConfig: The configuration instance.
        """
        return self._config
