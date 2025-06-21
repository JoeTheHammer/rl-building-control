from abc import ABC, abstractmethod
from typing import Dict

import gymnasium as gym
import numpy as np
import optuna
from gymnasium import Env

from controllers.base_controller import IController, IControllerProvider
from custom_loggers.setup_logger import logger
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment


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
    def _suggest_hyperparameters(self, trial: optuna.Trial) -> Dict:
        """
        Suggest a set of hyperparameters for the current Optuna trial.

        Args:
            trial (optuna.Trial): The current hyperparameter optimization trial.

        Returns:
            Dict: A dictionary of hyperparameter names and sampled values.
        """
        pass

    def _tune_hyperparameters(
        self,
        env_provider: IEnvironmentProvider,
        env_config: str,
        num_trials: int,
        num_episodes: int,
    ) -> Dict:
        """
        Run hyperparameter tuning using Optuna for a given environment setup.

        This will create a new environment and controller for each trial,
        run a short experiment to evaluate performance, and return the
        best-performing hyperparameter set.

        Args:
            env_provider (IEnvironmentProvider): Factory to create environments.
            env_config (str): Configuration key or path for environment creation.
            num_trials (int): Number of Optuna trials to run.

        Returns:
            Dict: The best hyperparameters found by Optuna.
        """

        def objective(trial: optuna.Trial) -> float:
            # Sample a fresh set of hyperparams
            trial_hp = self._suggest_hyperparameters(trial)

            # Build a new env & controller per trial
            env_t = env_provider.create_environment(env_config)
            env_t.continuous_action_space = True
            ctrl = self._build_controller(env_t, trial_hp)  # start from defaults

            # Evaluate with short experiment
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
        return study.best_params

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
        new_env.continuous_action_space = is_continuous_action_space

        hp = hyperparameters

        if hp is None:

            logger.info("No hyperparameters provided. Start with hyperparameter tuning.")

            hp = self._tune_hyperparameters(
                environment_provider, environment_config, num_trials, num_episodes
            )

            logger.info("Ended hyperparameter tuning.")
            logger.info(f"Best hyperparameters: {hp}")

        logger.info(f"Create controller with hyperparameters: {hp}")
        controller = self._build_controller(new_env, hp)

        # Training the controller that was already hyperparameter tuned.

        logger.info(f"Start training with {train_timesteps} timesteps.")
        controller.train(timesteps=train_timesteps)

        # Close env instance on which training was done on.
        controller.env.close()

        # Communicate to env that if this controller only supports continuous action spaces.
        env.continuous_action_space = is_continuous_action_space
        controller.env = env

        return controller
