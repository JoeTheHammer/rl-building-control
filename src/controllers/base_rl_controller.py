from abc import ABC, abstractmethod
from typing import Dict

import gymnasium as gym
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
            return Experiment(
                name="optuna_hyperparameter_tuning",
                env=env_t,
                controller=ctrl,
                num_episodes=num_episodes,
            ).run()

        study = optuna.create_study(direction="maximize")

        logger.info("Starting hyperparameter tuning.")

        study.optimize(objective, n_trials=num_trials)
        return study.best_params

    def create_controller(
        self,
        env: gym.Env,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
        train_timesteps: int = 1000,
        is_continuous_action_space: bool = False,
    ) -> IRLController:
        """
        Create, tune, and train an IRLController for a target environment.

        This method will:
          1. Instantiate a fresh environment via the provider.
          2. Run Optuna-based hyperparameter tuning.
          3. Build the controller with the best-found parameters.
          4. Train the controller for the specified number of timesteps.
          5. Attach the trained controller to the target environment.

        Args:
            env (gym.Env): The target environment the controller will control.
            config_path (str | None): Optional path for configuration (unused).
            environment_provider (IEnvironmentProvider | None): Factory for env creation.
            environment_config (str | None): Key or path for provider to load env.
            train_timesteps (int): Timesteps to train the controller after tuning.
            is_continuous_action_space (bool): Whether the action space is continuous.

        Returns:
            IRLController: A fully trained controller ready for use.
        """

        new_env = environment_provider.create_environment(environment_config)
        new_env.continuous_action_space = is_continuous_action_space

        best_hp = self._tune_hyperparameters(environment_provider, environment_config, 5, 1)
        logger.info("Ended hyperparameter tuning.")
        logger.info(f"Best hyperparameters: {best_hp}")

        controller = self._build_controller(new_env, best_hp)

        # Training the controller that was already hyperparameter tuned.
        controller.train(timesteps=train_timesteps)

        # Communicate to env that if this controller only supports continuous action spaces.
        env.continuous_action_space = is_continuous_action_space
        controller.env = env

        return controller
