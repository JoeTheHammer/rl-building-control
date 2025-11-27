from typing import Any, Dict, Optional, List

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import DDPG

from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import HPTunableControllerFactory
from controllers.base_rl_controller import (
    RLController,
    load_rl_controller_config,
)
from tuning.hp_tuning import tune_hp
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


class DDPGController(RLController):
    """
    Controller for the Deep Deterministic Policy Gradient (DDPG) algorithm.
    """

    def __init__(self, env: gym.Env, params: Dict):
        """
        Initializes the DDPG model with the given environment and parameters.
        """
        super().__init__(env)
        self.model = DDPG("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        """
        Predicts the action to take given the current state.
        """
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        """
        Trains the DDPG model for a specified number of timesteps.
        """
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class DDPGFactory(HPTunableControllerFactory):
    """
    Factory for the DDPGController with optional hyperparameter tuning support.
    """

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        """
        Discrete grid used for grid-search based hyperparameter tuning.
        Adapt as needed for your experiments.
        """
        return {
            "learning_rate": [1e-5, 5e-5, 1e-4, 5e-4, 1e-3],
            "gamma": [0.9, 0.95, 0.98, 0.99, 0.995],
            "batch_size": [32, 64, 128, 256],
            "tau": [0.001, 0.005, 0.01],
            "buffer_size": [100_000, 500_000, 1_000_000],
            "train_freq": [1, 2, 4],
            "gradient_steps": [1, 2, 4],
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        """
        Continuous / mixed search space for Optuna-based tuning.
        If trial is None, returns a good default configuration
        (basically what you are using now).
        """
        # Fallback / default config (your current settings)
        if trial is None:
            return {
                "learning_rate": 0.001,
                "gamma": 0.99,
                "buffer_size": 100_000,
                "tau": 0.005,
                "batch_size": 64,
                "train_freq": 1,
                "gradient_steps": 1,
            }

        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999, log=True),
            "buffer_size": trial.suggest_categorical(
                "buffer_size", [100_000, 300_000, 500_000, 1_000_000]
            ),
            "tau": trial.suggest_float("tau", 0.001, 0.02, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256, 512]),
            "train_freq": trial.suggest_categorical("train_freq", [1, 2, 4, 8]),
            "gradient_steps": trial.suggest_categorical("gradient_steps", [1, 2, 4, 8]),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DDPGController:
        """
        Builds and returns a new DDPGController instance.
        """
        return DDPGController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        """
        Creates the DDPG controller setup, loading configuration, creating the
        environment wrapper manager and (optionally) running HP tuning.
        """
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the DDPG controller.")

        config = load_rl_controller_config(self.config_path)

        # DDPG relies on a continuous action space.
        config.environment_wrapper.discrete_action = False
        config.environment_wrapper.continuous_action = True

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        hp = config.hyperparameters

        if config.hyperparameter_tuning is not None and config.hyperparameter_tuning.enabled:
            logger.info("Starting hyperparameter tuning for DDPG.")
            hp = tune_hp(
                self,
                hp_tuning_config=config.hyperparameter_tuning,
                env_wrapper_manager=env_wrap_manager,
                is_env_adapter=False,
                hp=config.hyperparameters,
            )
            logger.info(f"Finished hyperparameter tuning for DDPG. Best HP: {hp}")

        return super().create_rl_controller_setup(hp, env_wrap_manager)
