from typing import Any

from config.base_config import IEnvironmentConfig


class SinergymEnvironmentConfig(IEnvironmentConfig):
    """
    Concrete implementation of IEnvironmentConfig for the Sinergym environment.
    Stores paths and configuration objects needed to build the simulation environment.
    """

    def __init__(self, reward_cfg, action_cfg, state_cfg, model_path: str, weather_data_path: str):
        """
        Initialize a new SinergymEnvironmentConfig.

        Args:
            reward_cfg: Configuration parameters for the reward function.
            action_cfg: Configuration for the action space.
            state_cfg: Configuration for the state space.
            model_path (str): Path to the EnergyPlus IDF building model.
            weather_data_path (str): Path to the EPW weather file.
        """
        self._reward = reward_cfg
        self._action = action_cfg
        self._state = state_cfg
        self._model_path = model_path
        self._weather_data_path = weather_data_path

    def get_reward_config(self) -> Any:
        """
        Returns the reward configuration.

        Returns:
            Any: Reward function configuration (e.g., shaping parameters, penalties).
        """
        # TODO: Think of how to represent a reward function in the config.
        pass

    def get_action_space_config(self) -> Any:
        """
        Returns the action space configuration.

        Returns:
            Any: Action space definition (e.g., variables, ranges).
        """
        # TODO: Think of how to represent the action space in the config.
        pass

    def get_state_space_config(self) -> Any:
        """
        Returns the state space configuration.

        Returns:
            Any: State space definition (e.g., observable variables).
        """
        # TODO: Think of how to represent state space in the config.
        pass

    def get_building_model_config(self) -> str:
        """
        Returns the path to the building model file.

        Returns:
            str: Path to the EpJSON building model file.
        """
        return self._model_path

    def get_weather_data_config(self) -> str:
        """
        Returns the path to the weather data file.

        Returns:
            str: Path to the EPW weather file.
        """
        return self._weather_data_path
