from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Optional, cast

import gymnasium as gym
import numpy as np
import optuna
import yaml
from gymnasium.wrappers import NormalizeObservation, NormalizeReward
from pydantic import BaseModel
from stable_baselines3.common.monitor import Monitor

from controllers.base_controller import ControllerSetup, IController, IControllerProvider
from custom_loggers.setup_logger import logger
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment
from reporting.finder import find_reporting_wrapper
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.reporting_wrapper import ReportingWrapper


class Training(BaseModel):
    timesteps: int
    report_training: Optional[bool] = False
    report_denormalized_state: Optional[bool] = False


class HyperparameterTuning(BaseModel):
    enabled: Optional[bool] = False
    num_trials: int
    num_episodes: int


class RLControllerConfig(BaseModel):
    training: Training
    hyperparameter_tuning: Optional[HyperparameterTuning]
    hyperparameters: Optional[Dict[str, Any]] = None
    normalize_state: Optional[bool] = True
    normalize_reward: Optional[bool] = False


def wrap_env(
    env: gym.Env,
    normalize_state: bool,
    continuous_action_space: bool,
    normalize_reward: bool,
    use_tensorboard: bool = False,
) -> gym.Env:
    if normalize_state:
        env = NormalizeObservation(env)
    if continuous_action_space:
        env = ContinuousActionWrapper(env)
    if normalize_reward:
        env = NormalizeReward(env)
    if use_tensorboard:
        env = Monitor(env)
    return env


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
    reporting_wrapper = find_reporting_wrapper(env)

    if enabled and reporting_wrapper:
        reporting_wrapper.start_recording()
        try:
            yield
        finally:
            logger.info("Training finished. Ending recording and generating reports...")
            reporting_wrapper.end_recording()
            reporting_wrapper.create_plots(output_dir=output_dir)
            reporting_wrapper.export_to_csv(output_dir="./csv-training")
    else:
        if enabled and not reporting_wrapper:
            logger.warning("Reporting is enabled, but no ReportingWrapper was found.")
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
    def _build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> IRLController:
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

        return {}

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
        normalize_state: bool = False,
        normalize_reward: bool = False,
        on_policy: bool = False,
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

            if on_policy:
                # If on policy the wrapping will be done later in the adapter.
                env_t = wrap_env(env_t, False, is_continuous_action_space, False)
            else:
                env_t = wrap_env(
                    env_t, normalize_state, is_continuous_action_space, normalize_reward
                )

            ctrl = self._build_controller(env_t, trial_hp, normalize_reward=normalize_reward)

            if on_policy:
                # If on policy adapter is returned by build_controller that serves as controller and env.
                env_t = ctrl

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

    def _get_final_hyperparameters(
        self,
        config: RLControllerConfig,
        environment_provider: IEnvironmentProvider,
        environment_config: str,
        on_policy: bool,
        is_continuous_action_space: bool,
        normalize_state: bool,
        normalize_reward: bool,
    ) -> Dict[str, Any]:
        """Handles the optional hyperparameter tuning process and returns the final set of hyperparameters."""
        hp = config.hyperparameters or {}
        tuning_config = config.hyperparameter_tuning

        # Proceed with tuning only if it's enabled and supported by the controller.
        if tuning_config and tuning_config.enabled:
            if not self._suggest_hyperparameters_space():
                logger.warning(
                    f"Hyperparameter tuning is enabled, but not supported by {self.__class__.__name__}. "
                    "Using parameters from the config file."
                )
                return hp

            logger.info("Hyperparameter tuning enabled and supported. Starting tuning process.")
            hp = self._tune_hyperparameters(
                env_provider=environment_provider,
                env_config=environment_config,
                num_trials=tuning_config.num_trials,
                num_episodes=tuning_config.num_episodes,
                is_continuous_action_space=is_continuous_action_space,
                normalize_state=normalize_state,
                normalize_reward=normalize_reward,
                on_policy=on_policy,
                fixed_hyperparams=hp,
            )
            logger.info(f"Ended hyperparameter tuning. Best hyperparameters: {hp}")

        return hp

    def _setup_on_policy_controller(
        self,
        hp: Dict[str, Any],
        training_config: Training,
        environment_provider: IEnvironmentProvider,
        environment_config: str,
        is_continuous_action_space: bool,
        normalize_reward: bool,
    ) -> ControllerSetup:
        """Builds, trains, and sets up an on-policy controller."""
        env = environment_provider.create_environment(environment_config)

        if is_continuous_action_space:
            env = ContinuousActionWrapper(env)

        # Determine if monitor wrapper should be added to get full functionality of tensorboard
        # used to monitor training.
        if "tensorboard_log" in hp and hp["tensorboard_log"]:
            env = Monitor(env)

        adapter = self._build_controller(
            env,
            hp,
            normalize_reward=normalize_reward,
            report_denormalized_state=training_config.report_denormalized_state,
        )

        with reporting_context(adapter, training_config.report_training):
            logger.info(f"Start training with {training_config.timesteps} timesteps.")
            adapter.train(timesteps=training_config.timesteps)

        if isinstance(adapter, gym.Env) and isinstance(adapter, IController):
            return ControllerSetup(adapter, cast(gym.Env, adapter))

        raise RuntimeError("On-policy adapter must be both a Controller and an Environment.")

    def _setup_off_policy_controller(
        self,
        hp: Dict[str, Any],
        training_config: Training,
        environment_provider: IEnvironmentProvider,
        environment_config: str,
        normalize_state: bool,
        is_continuous_action_space: bool,
        normalize_reward: bool,
    ) -> ControllerSetup:
        """Builds, trains, and sets up an off-policy controller."""
        # Setup environment for training
        training_env = environment_provider.create_environment(environment_config)

        # Determine if monitor wrapper should be added to get full functionality of tensorboard
        # used to monitor training.
        use_tensorboard = "tensorboard_log" in hp and hp["tensorboard_log"]

        training_env = wrap_env(
            training_env,
            normalize_state,
            is_continuous_action_space,
            normalize_reward,
            use_tensorboard,
        )
        if training_config.report_training:
            training_env = ReportingWrapper(
                training_env, denorm_state=training_config.report_denormalized_state
            )

        # Build and train the controller
        controller = self._build_controller(training_env, hp)
        logger.info(f"Start training with {training_config.timesteps} timesteps.")
        with reporting_context(training_env, training_config.report_training):
            controller.train(timesteps=training_config.timesteps)
        training_env.close()

        # Setup final environment for evaluation
        final_env = environment_provider.create_environment(environment_config)
        final_env = wrap_env(
            final_env, normalize_state, is_continuous_action_space, normalize_reward
        )
        controller.env = final_env
        return ControllerSetup(controller, final_env)

    def create_rl_controller_setup(
        self,
        config: RLControllerConfig,
        normalize_state: bool = False,
        is_continuous_action_space: bool = False,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
        on_policy: bool = False,
        normalize_reward: bool = False,
    ) -> ControllerSetup:
        """Orchestrates the setup and training of a reinforcement learning controller.

        This method serves as the main entry point for creating a controller.
        It finalizes hyperparameters, performs tuning if configured, builds the
        model, and runs the training process. It correctly handles the distinct
        workflows for on-policy and off-policy algorithms, returning a fully
        trained controller and its curresponding environment ready for evaluation.

        Args:
            config: The configuration object parsed from the YAML file, containing
                training, tuning, and hyperparameter settings.
            normalize_state: If True, applies observation normalization to the
                environment. Defaults to False.
            is_continuous_action_space: If True, wraps the environment to ensure
                a continuous action space. Defaults to False.
            environment_provider: The provider class used to create environment
                instances for tuning and training.
            environment_config: The configuration string or path passed to the
                environment provider to create an environment.
            on_policy: If True, the on-policy setup workflow is used. If False,
                the off-policy workflow is used. Defaults to False.
            normalize_reward: If True, applies reward normalization to the
                environment. Defaults to False.

        Returns:
            A `ControllerSetup` object containing the fully trained controller
            and its final evaluation environment.

        Raises:
            ValueError: If no hyperparameters are provided in the configuration
                and hyperparameter tuning is either disabled or not supported
                by the controller.
        """

        final_hp = self._get_final_hyperparameters(
            config=config,
            environment_provider=environment_provider,
            environment_config=environment_config,
            on_policy=on_policy,
            is_continuous_action_space=is_continuous_action_space,
            normalize_state=normalize_state,
            normalize_reward=normalize_reward,
        )

        if not final_hp:
            raise ValueError(
                "No hyperparameters provided and tuning was not enabled/supported. "
                "Cannot create a controller without hyperparameters."
            )

        logger.info(f"\033[92mCreate controller with hyperparameters: {final_hp}\033[0m")

        if on_policy:
            return self._setup_on_policy_controller(
                hp=final_hp,
                training_config=config.training,
                environment_provider=environment_provider,
                environment_config=environment_config,
                is_continuous_action_space=is_continuous_action_space,
                normalize_reward=normalize_reward,
            )
        else:
            return self._setup_off_policy_controller(
                hp=final_hp,
                training_config=config.training,
                environment_provider=environment_provider,
                environment_config=environment_config,
                normalize_state=normalize_state,
                is_continuous_action_space=is_continuous_action_space,
                normalize_reward=normalize_reward,
            )
