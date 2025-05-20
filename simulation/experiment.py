from custom_loggers.setup_logger import logger as setup_logger


class ExperimentConfig:
    """
    Represents a single experiment configuration.

    Attributes:
        name (str): The name of the experiment.
        engine (str): The name of the environment engine (e.g., 'sinergym').
        environment_config (str): The path to the environment configuration file.
    """

    def __init__(self, name: str, engine: str, environment_config: str):
        if not name or not engine or not environment_config:
            setup_logger.error("Missing required experiment configuration fields.")
            raise ValueError("All fields (name, engine, environment_config) must be provided.")

        self.name = name
        self.engine = engine
        self.environment_config = environment_config


class Experiment:
    def __init__(self):
        pass

    def run(self):
        pass
