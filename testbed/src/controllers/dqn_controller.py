from typing import Any, Dict, Optional, List

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import DQN

from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import HPTunableControllerFactory
from controllers.base_rl_controller import (
    RLController,
    load_rl_controller_config,
)
from tuning.hp_tuning import tune_hp
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


class DQNController(RLController):
    """
    Controller for the Deep Q-Network (DQN) algorithm.
    SB3 DQN is Double-DQN by default.
    """

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)
        self.model = DQN("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state, deterministic=True)
        return action

    def train(self, timesteps: int):
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class DQNFactory(HPTunableControllerFactory):
    """
    Factory for DQN with hyperparameter tuning support.
    """

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        return {
            "learning_rate": [1e-5, 5e-5, 1e-4, 3e-4, 1e-3],
            "gamma": [0.9, 0.95, 0.98, 0.99],
            "batch_size": [32, 64, 128, 256],
            "buffer_size": [50_000, 100_000, 200_000, 500_000],
            "learning_starts": [500, 1000, 2000],
            "train_freq": [1, 4, 8],
            "gradient_steps": [1, 2, 4],
            "target_update_interval": [500, 1000, 5000],
            "exploration_fraction": [0.05, 0.1, 0.2],
            "exploration_final_eps": [0.01, 0.05, 0.1],
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:

        if trial is None:
            return {
                "learning_rate": 0.0001,
                "gamma": 0.99,
                "buffer_size": 50000,
                "learning_starts": 1000,
                "batch_size": 32,
                "target_update_interval": 1000,
                "exploration_fraction": 0.1,
                "exploration_final_eps": 0.05,
                "exploration_initial_eps": 1.0,
                "train_freq": 4,
                "gradient_steps": 1,
            }

        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.90, 0.999, log=True),
            "buffer_size": trial.suggest_categorical(
                "buffer_size", [50_000, 100_000, 200_000, 500_000]
            ),
            "learning_starts": trial.suggest_int("learning_starts", 500, 5000),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256]),
            "target_update_interval": trial.suggest_categorical(
                "target_update_interval", [500, 1000, 2500, 5000]
            ),
            "train_freq": trial.suggest_categorical("train_freq", [1, 4, 8]),
            "gradient_steps": trial.suggest_categorical("gradient_steps", [1, 2, 4]),
            "exploration_fraction": trial.suggest_float("exploration_fraction", 0.05, 0.3),
            "exploration_initial_eps": 1.0,  # Always stays 1.0
            "exploration_final_eps": trial.suggest_float("exploration_final_eps", 0.01, 0.1),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DQNController:
        return DQNController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the DQN controller.")

        config = load_rl_controller_config(self.config_path)

        # DQN must always use discrete actions
        config.environment_wrapper.discrete_action = True
        config.environment_wrapper.continuous_action = False

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        hp = config.hyperparameters

        if config.hyperparameter_tuning is not None and config.hyperparameter_tuning.enabled:
            logger.info("Starting hyperparameter tuning for DQN...")
            hp = tune_hp(
                self,
                hp_tuning_config=config.hyperparameter_tuning,
                env_wrapper_manager=env_wrap_manager,
                is_env_adapter=False,
                hp=config.hyperparameters,
            )
            logger.info(f"Finished hyperparameter tuning for DQN. Best HP: {hp}")

        return super().create_rl_controller_setup(hp, env_wrap_manager)
