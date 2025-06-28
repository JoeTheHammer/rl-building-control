from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import gymnasium as gym
import numpy as np
import optuna
from gymnasium import Env

from controllers.base_controller import IController, IControllerProvider
from custom_loggers.setup_logger import logger
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment
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


class IRLControllerProvider(IControllerProvider, ABC):
    """
    Provider for IRLController instances, including hyperparameter tuning
    and controller creation logic.
    """

    @abstractmethod
    def _build_controller(self, env: Env, hyper_params: Dict) -> IRLController:
        """
        Construct an IRLController with the given environment and hyperparameters.

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
            env_t.unwrapped.continuous_action_space = is_continuous_action_space
            ctrl = self._build_controller(env_t, trial_hp)
            rewards = Experiment(
                name="hyperparameter_tuning",
                env=env_t,
                controller=ctrl,
                num_episodes=num_episodes,
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
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
        train_timesteps: int = 1000,
        is_continuous_action_space: bool = False,
        num_trials: int | None = 20,
        num_episodes: int | None = 2,
        hyperparameters: Dict | None = None,
    ) -> IRLController:
        """
        Create and train a reinforcement learning controller.

        If no hyperparameters are provided, Optuna-based hyperparameter tuning will be performed.
        The controller will be built using the resulting or provided hyperparameters, trained for
        a specified number of timesteps, and linked back to the given environment.

        Args:
            env (gym.Env): The target environment instance to associate with the trained controller.
            environment_provider (IEnvironmentProvider | None): Provider responsible for generating
                new instances of the environment.
            environment_config (str | None): Path to the environment configuration file.
            train_timesteps (int): Number of timesteps to train the controller.
            is_continuous_action_space (bool): Whether the controller and environment should use
                a continuous action space.
            num_trials (int | None): Number of trials for hyperparameter tuning, if enabled.
            num_episodes (int | None): Number of evaluation episodes per trial during tuning.
            hyperparameters (Dict | None): Optional pre-defined hyperparameters for the controller.
                If None, hyperparameter tuning is triggered.

        Returns:
            IRLController: A trained reinforcement learning controller instance.
        """

        new_env = environment_provider.create_environment(environment_config)
        new_env.unwrapped.continuous_action_space = is_continuous_action_space

        hp = hyperparameters

        # Perform hyperparameter tuning if no hyperparameters are provided,
        # or if the provided set is incomplete (i.e., does not contain all required keys).
        if hp is None or len(hp) is not len(self._suggest_hyperparameters()):

            logger.info("Not all hyperparameters provided. Start with hyperparameter tuning.")

            hp = self._tune_hyperparameters(
                environment_provider,
                environment_config,
                num_trials,
                num_episodes,
                is_continuous_action_space=is_continuous_action_space,
                fixed_hyperparams=hyperparameters or {},
            )

            logger.info("Ended hyperparameter tuning.")
            logger.info(f"Best hyperparameters: {hp}")

        logger.info(f"\033[92mCreate controller with hyperparameters: {hp}\033[0m")

        wrapped_env = ReportingWrapper(new_env)
        controller = self._build_controller(wrapped_env, hp)

        logger.info(f"Start training with {train_timesteps} timesteps.")
        wrapped_env.start_recording()
        controller.train(timesteps=train_timesteps)
        wrapped_env.end_recording()
        wrapped_env.create_plots()

        # Plug out reporting wrapper.
        controller.env = wrapped_env.env

        # Close env instance on which training was done on.
        controller.env.close()

        # Communicate to env that if this controller only supports continuous action spaces.
        env.unwrapped.continuous_action_space = is_continuous_action_space

        # Set new environment
        controller.env = env

        return controller
