from typing import Any, Dict, Optional, List

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import TD3

from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import HPTunableControllerFactory
from controllers.base_rl_controller import (
    RLController,
    load_rl_controller_config,
)
from tuning.hp_tuning import tune_hp
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


class TD3Controller(RLController):
    """
    Controller for the Twin Delayed Deep Deterministic Policy Gradient (TD3) algorithm.
    """

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)
        self.model = TD3("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state, deterministic=True)
        return action

    def train(self, timesteps: int):
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class TD3Factory(HPTunableControllerFactory):
    """
    TD3 controller factory with full Optuna/grid-search hyperparameter tuning support.
    """

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        return {
            "learning_rate": [1e-5, 5e-5, 1e-4, 3e-4, 1e-3],
            "gamma": [0.9, 0.95, 0.98, 0.99],
            "batch_size": [64, 128, 256, 512],
            "buffer_size": [200_000, 500_000, 1_000_000],
            "tau": [0.001, 0.005, 0.01],
            "train_freq": [1, 2, 4],
            "gradient_steps": [1, 2, 4],
            "policy_delay": [1, 2, 3],
            "target_policy_noise": [0.1, 0.2],
            "target_noise_clip": [0.3, 0.5],
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:

        # Default fallback (your current configuration)
        if trial is None:
            return {
                "learning_rate": 0.0003,
                "gamma": 0.99,
                "buffer_size": 1_000_000,
                "tau": 0.005,
                "batch_size": 256,
                "policy_delay": 2,
                "train_freq": 1,
                "gradient_steps": 1,
                "target_policy_noise": 0.2,
                "target_noise_clip": 0.5,
            }

        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.90, 0.999, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [64, 128, 256, 512]),
            "buffer_size": trial.suggest_categorical("buffer_size", [200_000, 500_000, 1_000_000]),
            "tau": trial.suggest_float("tau", 0.001, 0.02, log=True),
            "train_freq": trial.suggest_categorical("train_freq", [1, 2, 4, 8]),
            "gradient_steps": trial.suggest_categorical("gradient_steps", [1, 2, 4, 8]),
            "policy_delay": trial.suggest_int("policy_delay", 1, 3),
            "target_policy_noise": trial.suggest_float("target_policy_noise", 0.05, 0.3),
            "target_noise_clip": trial.suggest_float("target_noise_clip", 0.2, 0.6),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> TD3Controller:
        return TD3Controller(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the TD3 controller.")

        config = load_rl_controller_config(self.config_path)

        # TD3 always uses a continuous action space
        config.environment_wrapper.discrete_action = False
        config.environment_wrapper.continuous_action = True

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        hp = config.hyperparameters

        if config.hyperparameter_tuning is not None and config.hyperparameter_tuning.enabled:
            logger.info("Starting hyperparameter tuning for TD3...")
            hp = tune_hp(
                self,
                hp_tuning_config=config.hyperparameter_tuning,
                env_wrapper_manager=env_wrap_manager,
                is_env_adapter=False,
                hp=config.hyperparameters,
            )
            logger.info(f"Finished hyperparameter tuning for TD3. Best HP: {hp}")

        return super().create_rl_controller_setup(hp, env_wrap_manager)
