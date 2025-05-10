from abc import ABC, abstractmethod
from typing import Any


class IEnvironmentConfig(ABC):
    """
    Interface for configuring an environment. Concrete implementations
    must define how to retrieve configurations for reward function,
    action space, state space, building model, and weather data. This interface
    is designed to be open and flexible, allowing future developers complete
    freedom in defining the configurations required for newly implemented environments.
    """

    @abstractmethod
    def get_reward_config(self) -> Any:
        """
        Returns the reward configuration.
        This may include weights, thresholds, or any other structure
        needed to calculate the reward signal for the environment.

        Returns:
            Any: The configuration used by the reward function.
        """
        pass

    @abstractmethod
    def get_action_space_config(self) -> Any:
        """
        Returns the configuration for the action space.
        This may include discrete or continuous action definitions
        or variables in the simulator that are target of an action.

        Returns:
            Any: The configuration used to define the agent's action space.
        """
        pass

    @abstractmethod
    def get_state_space_config(self) -> Any:
        """
        Returns the configuration for the state space.
        This may include variables in the simulator that can be read during
        simulation.

        Returns:
            Any: The configuration used for environment observations.
        """
        pass

    @abstractmethod
    def get_building_model_config(self) -> Any:
        """
        Returns the configuration for the building model.
        For example, this could reference a model file or
        building-specific metadata.

        Returns:
            Any: The configuration for the physical model of the environment.
        """
        pass

    @abstractmethod
    def get_weather_data_config(self) -> Any:
        """
        Returns the configuration for the weather data.
        This could be a path to a weather file.

        Returns:
            Any: The configuration for environmental/weather inputs.
        """
        pass
