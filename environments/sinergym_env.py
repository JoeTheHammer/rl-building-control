from sinergym.envs import EplusEnv


class SinergymEnvironmentConfig:
    def __init__(self, weather_data_path, building_model_path):
        self.weather_data_path = weather_data_path
        self.building_model_path = building_model_path


class SinergymEnvironment(EplusEnv):
    def __init__(self):
        pass
