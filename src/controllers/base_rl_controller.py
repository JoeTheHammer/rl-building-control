from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Optional

import gymnasium as gym
import numpy as np
import optuna
import yaml
from gymnasium import Env
from pydantic import BaseModel

from controllers.base_controller import IController, IControllerProvider
from custom_loggers.setup_logger import logger
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.reporting_wrapper import ReportingWrapper


class Training(BaseModel):
    timesteps: int
    report_training: Optional[bool] = False
    report_denormalized_state: Optional[bool] = False


class HyperparameterTuning(BaseModel):
    num_trials: int
    num_episodes: int


class RLControllerConfig(BaseModel):
    training: Training
    hyperparameter_tuning: HyperparameterTuning
    hyperparameters: Optional[Dict[str, Any]] = None


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
def reporting_context(env, enabled, output_dir="./plots-training"):
    if enabled:
        env.start_recording()
        try:
            yield
        finally:
            env.end_recording()
            env.create_plots(output_dir=output_dir)
    else:
        yield


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


class IRLControllerProvider(IControllerProvider, ABC):
    """
    Provider for IRLController instances, including hyperparameter tuning
    and controller creation logic.
    """

    @abstractmethod
    def _build_controller(self, env: Env, hyper_params: Dict) -> IRLController:
        """
        Construct an IRLController with the given environment and hyperparameters. Used during
        hyperparameter tuning and to to build final controller.

        Args:
            env (Env): The Gym environment the controller will operate in.
            hyper_params (Dict): Mapping of hyperparameter names to values.

        Returns:
            IRLController: A new, untrained controller instance.
        """
        pass

    @abstractmethod
    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:
        """
        Suggest a set of hyperparameters available for this controller.

        Args:
            trial (optuna.Trial | None): The current Optuna trial. If None, defaults are used.

        Returns:
            Dict: Dictionary containing suggested or fixed hyperparameters.
        """

        pass

    def _suggest_hyperparameters(
        self, trial: Optional[optuna.Trial] = None, fixed_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        fixed_params = fixed_params or {}

        # First suggest everything using Optuna
        suggested = self._suggest_hyperparameters_space(trial)

        # Then override with anything the user has fixed
        return {**suggested, **fixed_params}

    def _tune_hyperparameters(
        self,
        env_provider: IEnvironmentProvider,
        env_config: str,
        num_trials: int,
        num_episodes: int,
        is_continuous_action_space: bool = False,
        fixed_hyperparams: Dict[str, Any] = None,
    ) -> Dict:
        """
        Run hyperparameter tuning using Optuna for a given environment setup.

        This will:
        - Create a new environment and controller for each trial
        - Respect fixed hyperparameters and tune the rest
        - Evaluate controller performance using a short experiment
        - Return the best-performing combination of fixed and tuned hyperparameters

        Returns:
            Dict: Combined dictionary of tuned and fixed hyperparameters.
        """

        fixed_hyperparams = fixed_hyperparams or {}

        def objective(trial: optuna.Trial) -> float:
            trial_hp = self._suggest_hyperparameters(trial, fixed_hyperparams)

            logger.info(f"Test with these hp: {trial_hp}")

            env_t = env_provider.create_environment(env_config)

            if is_continuous_action_space:
                # Controller only supports continuous action space.
                env_t = ContinuousActionWrapper(env_t)

            ctrl = self._build_controller(env_t, trial_hp)
            rewards = Experiment(
                name="hyperparameter_tuning",
                env=env_t,
                controller=ctrl,
                episodes=num_episodes,
            ).run()
            env_t.close()
            return float(np.mean(rewards))

        study = optuna.create_study(direction="maximize")
        logger.info("Starting hyperparameter tuning.")
        study.optimize(objective, n_trials=num_trials)
        return {**study.best_params, **fixed_hyperparams}

    def create_rl_controller(
        self,
        env: gym.Env,
        config: RLControllerConfig,
        is_continuous_action_space: bool = False,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> IRLController:
        """Creates, optionally tunes, and trains a reinforcement learning controller.

        This method orchestrates the entire lifecycle of an RL controller based on a
        provided configuration file. The process includes:
        1.  Loading controller configuration (hyperparameters, tuning, training settings).
        2.  Creating a dedicated environment for training.
        3.  Performing hyperparameter tuning if parameters are missing or incomplete.
        4.  Building the controller with the finalized hyperparameters.
        5.  Wrapping the environment for specific action spaces or reporting.
        6.  Training the controller for a specified number of timesteps.
        7.  Setting the final evaluation environment on the trained controller.

        Args:
            env: The primary Gymnasium environment the controller will operate on after training.
            config: The configuration object parsed from the YAML configuration file.
            is_continuous_action_space: A flag to indicate if the environment's action
                space should be wrapped to be continuous. Defaults to False.
            environment_provider: An optional provider class used to create separate
                environments for hyperparameter tuning and training.
            environment_config: An optional configuration string or path passed to the
                environment provider.

        Returns:
            A fully trained and configured IRLController instance, ready for inference.
        """

        tuning = config.hyperparameter_tuning
        hyperparameters = config.hyperparameters
        training = config.training

        training_env = environment_provider.create_environment(environment_config)

        hp = hyperparameters

        # Perform hyperparameter tuning if no hyperparameters are provided,
        # or if the provided set is incomplete (i.e., does not contain all required keys).
        if hp is None or len(hp) is not len(self._suggest_hyperparameters()):

            logger.info("Not all hyperparameters provided. Start with hyperparameter tuning.")

            hp = self._tune_hyperparameters(
                environment_provider,
                environment_config,
                tuning.num_trials if tuning else None,
                tuning.num_episodes if tuning else None,
                is_continuous_action_space=is_continuous_action_space,
                fixed_hyperparams=hyperparameters or {},
            )

            logger.info("Ended hyperparameter tuning.")
            logger.info(f"Best hyperparameters: {hp}")

        logger.info(f"\033[92mCreate controller with hyperparameters: {hp}\033[0m")

        if is_continuous_action_space:
            # Controller only supports continuous action space.
            training_env = ContinuousActionWrapper(training_env)

        if training.report_training:
            training_env = ReportingWrapper(
                training_env, denorm_state=training.report_denormalized_state
            )

        controller = self._build_controller(training_env, hp)

        logger.info(f"Start training with {training.timesteps} timesteps.")

        with reporting_context(training_env, training.report_training):
            controller.train(timesteps=training.timesteps)

        # Close env instance on which training was done on.
        training_env.close()

        if is_continuous_action_space:
            # Controller only supports continuous action space.
            env = ContinuousActionWrapper(env)

        # Set new environment
        controller.env = env

        return controller
