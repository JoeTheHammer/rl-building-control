from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, cast

import gymnasium as gym
import yaml
from stable_baselines3.common.monitor import Monitor

from controllers.base_controller import ControllerSetup, IController, IControllerFactory
from controllers.config import RLControllerConfig
from custom_loggers.setup_logger import logger
from wrappers.manager import EnvWrapperManager
from wrappers.reporting_wrapper import ReportingWrapper


class IRLController(IController, ABC):
    """
    Base interface for a Reinforcement Learning (IRL) controller.
    """

    @abstractmethod
    def train(self, timesteps: int):
        """
        Train the controller for a specified number of timesteps.

        Args:
            timesteps (int): The number of environment steps to use for training.
        """
        pass


@contextmanager
def reporting_context(env, enabled, report_denormalized_state, output_dir="./plots-training"):
    """
    A context manager to wrap an environment with reporting capabilities.
    """
    if not enabled:
        # If reporting is disabled, just yield the original environment and do nothing else.
        yield env
        return

    # If enabled, wrap the environment and set up reporting.
    reporting_wrapper = ReportingWrapper(env, denorm_state=report_denormalized_state)
    reporting_wrapper.start_recording()

    try:
        # Yield the wrapped environment for use inside the 'with' block.
        yield reporting_wrapper
    finally:
        # This code runs after the 'with' block is exited, for cleanup.
        logger.info("Training finished. Ending recording and generating reports...")
        reporting_wrapper.end_recording()
        reporting_wrapper.create_plots(output_dir=output_dir)
        reporting_wrapper.export_to_csv(output_dir="./csv-training")


def load_rl_controller_config(path: str) -> RLControllerConfig:
    """
    Loads a YAML controller configuration file and parses it into a SACControllerConfig object.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        SACControllerConfig: Parsed configuration object.
    """
    with open(path, "r") as f:
        raw_data = yaml.safe_load(f)
    return RLControllerConfig(**raw_data)


class IRLControllerFactory(IControllerFactory, ABC):
    """
    Factory for IRLController instances, including hyperparameter tuning
    and controller creation logic.
    """

    @abstractmethod
    def build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> IRLController:
        """
        Construct an IRLController with the given environment and hyperparameters. Used during
        hyperparameter tuning and to build final controller.

        Args:
            env (Env): The Gym environment the controller will operate in.
            hyper_params (Dict): Mapping of hyperparameter names to values.

        Returns:
            IRLController: A new, untrained controller instance.
        """
        pass

    def create_rl_controller_setup_new(
            self,
            hp: Dict[str, Any],
            env_wrap_manager: EnvWrapperManager,
            is_env_adapter: bool = False,
    ) -> ControllerSetup:

        logger.info(f"\033[92mCreate controller with hyperparameters: {hp}\033[0m")

        env = self.env_factory.create_environment()
        env = env_wrap_manager.apply_wrappers(env)

        use_tensorboard = bool(hp.get("tensorboard_log"))

        if use_tensorboard:
            env_wrap_manager.add_wrapper(Monitor)

        controller = self.build_controller(env, hp)
        training_conf = load_rl_controller_config(self.config_path).training

        with reporting_context(env, training_conf.report_training, training_conf.report_denormalized_state):
            logger.info(f"Start training with {training_conf.timesteps} timesteps.")
            controller.train(timesteps=training_conf.timesteps)

        if is_env_adapter:
            if isinstance(controller, gym.Env) and isinstance(controller, IController):
                return ControllerSetup(controller, cast(gym.Env, controller))
            raise RuntimeError("On-policy adapter must be both a Controller and an Environment.")

        return ControllerSetup(controller, controller.env)
