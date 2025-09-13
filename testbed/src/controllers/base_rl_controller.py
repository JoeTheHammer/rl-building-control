from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, cast

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


def load_rl_controller_config(path: str) -> RLControllerConfig:
    """
    Loads a YAML controller configuration file and parses it into a RLControllerConfig object.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        RLControllerConfig: Parsed configuration object.
    """
    with open(path, "r") as f:
        raw_data = yaml.safe_load(f)
    return RLControllerConfig(**raw_data)


def find_reporting_wrapper(env: gym.Env) -> Optional[ReportingWrapper]:
    """
    Traverses the environment wrapper stack to find an instance of ReportingWrapper.

    Args:
        env (gym.Env): The environment (potentially wrapped).

    Returns:
        Optional[ReportingWrapper]: The wrapper instance if found, otherwise None.
    """
    current_env = env
    while hasattr(current_env, "env"):
        if isinstance(current_env, ReportingWrapper):
            return current_env
        current_env = current_env.env
    return None


class IRLControllerFactory(IControllerFactory, ABC):
    """
    Factory for IRLController instances, including hyperparameter tuning
    and controller creation logic.
    """

    @abstractmethod
    def build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> IRLController:
        """
        Construct an IRLController with the given environment and hyperparameters.

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
        """
        Builds, trains, and sets up a reinforcement learning controller.
        """
        logger.info(f"\033[92mCreate controller with hyperparameters: {hp}\033[0m")

        # --- Environment Setup: Wrap everything BEFORE building the controller ---
        env = self.env_factory.create_environment()
        env = env_wrap_manager.apply_wrappers(env)

        training_conf = load_rl_controller_config(self.config_path).training

        if bool(hp.get("tensorboard_log")):
            env = Monitor(env)

        if training_conf.report_training:
            env = ReportingWrapper(env, denorm_state=training_conf.report_denormalized_state)

        controller = self.build_controller(env, hp)

        # --- Training ---
        logger.info(f"Start training with {training_conf.timesteps} timesteps.")
        reporting_wrapper = find_reporting_wrapper(controller.env)

        try:
            if reporting_wrapper:
                reporting_wrapper.start_recording()
            controller.train(timesteps=training_conf.timesteps)
        finally:
            if reporting_wrapper:
                logger.info("Training finished. Ending recording and generating reports...")
                reporting_wrapper.end_recording()
                reporting_wrapper.create_plots(output_dir="./plots-training")
                reporting_wrapper.export_to_csv(output_dir="./csv-training")

        if is_env_adapter:
            if isinstance(controller, gym.Env) and isinstance(controller, IController):
                return ControllerSetup(controller, cast(gym.Env, controller))
            raise RuntimeError("Adapter must be both a Controller and an Environment.")

        return ControllerSetup(controller, controller.env)
