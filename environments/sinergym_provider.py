from environments.base_provider import EnvironmentProvider
from environments.sinergym_env import SinergymEnvironment


class SinergymProvider(EnvironmentProvider):

    def create_environment(self, config_path: str) -> SinergymEnvironment:
        # TODO: Read configuration, use configuration to build sinergym environment, return this
        pass
