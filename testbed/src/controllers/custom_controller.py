import importlib
from pathlib import Path
from typing import Dict, Optional, Union

import yaml
from pydantic import BaseModel

from controllers.base_controller import ControllerSetup, Controller, ControllerFactory
from utils.seeding import seed_env_spaces


class CustomControllerConfig(BaseModel):
    module: str
    class_name: str
    args: Optional[Dict[str, Union[float, int, str, bool]]] = None


def parse_custom_controller_config(config_path: str) -> CustomControllerConfig:
    if not Path(config_path).is_file():
        raise FileNotFoundError(f"{config_path} not found")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return CustomControllerConfig(**data)


class CustomControllerFactory(ControllerFactory):
    def create_controller_setup(self) -> ControllerSetup:

        if self.config_path == "":
            raise FileNotFoundError(f"{self.config_path} not found")

        controller_config = parse_custom_controller_config(self.config_path)

        try:
            module = importlib.import_module(controller_config.module)
            controller_class = getattr(module, controller_config.class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Could not import class '{controller_config.class_name}' "
                f"from module '{controller_config.module}': {e}"
            ) from e

        # Check if passed controller class inherits from IController.
        if not issubclass(controller_class, Controller):
            raise TypeError(
                f"The class '{controller_class.__name__}' in module "
                f"'{controller_config.module}' must inherit from 'IController'."
            )

        controller_args = controller_config.args or {}

        env = self.env_factory.create_environment()
        seed_env_spaces(env, self.seed)

        controller_instance = controller_class(env=env, **controller_args)

        return ControllerSetup(controller_instance, env)
