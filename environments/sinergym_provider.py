from parser.config_parser import parse_sinergym_environment_config

from environments.base_provider import EnvironmentProvider
from environments.sinergym_env import SinergymEnvironment


class SinergymProvider(EnvironmentProvider):

    def create_environment(self, config_path: str) -> SinergymEnvironment:
        # TODO: Read configuration, use configuration to build sinergym environment, return this
        config = parse_sinergym_environment_config(config_path)
        print(config.action_space.actuators)
        print(config.state_space.meters)
        print(config.weather_data)
        print(config.building_model)
        pass
