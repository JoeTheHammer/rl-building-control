from typing import Any, Dict, Optional, List

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import SAC

from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import HPTunableControllerFactory
from controllers.base_rl_controller import (
    RLController,
    load_rl_controller_config,
)
from tuning.hp_tuning import tune_hp
from wrappers.manager import EnvWrapperManager


class SACController(RLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)

        self.model = SAC("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        # Set log_interval to 1 to increase support for tensor graph integration (more regular logs).
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class SACFactory(HPTunableControllerFactory):

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        return {
            "learning_rate": [1e-5, 5e-5, 1e-4, 5e-4, 1e-3],
            "gamma": [0.9, 0.95, 0.98, 0.99, 0.995],
            "batch_size": [32, 64, 128, 256],
            "ent_coef": ["auto_0.5", "auto_1.0", "auto_2.0"],
            "tau": [0.005, 0.01, 0.02],  # target smoothing coefficient
            "train_freq": [1, 2, 4],  # how often to update (per step)
            "gradient_steps": [1, 2, 4],  # how many gradient steps per update
            "target_update_interval": [1, 10],  # how often to update target network
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        if trial is None:
            return {
                "ent_coef": "auto_2.0",
                "learning_rate": 0.0009851008761417273,
                "gamma": 0.9305074409820552,
                "batch_size": 32,
                "tau": 0.005,
                "train_freq": 1,
                "gradient_steps": 1,
                "target_update_interval": 1,
            }

        ent_coef_scale = trial.suggest_float("ent_coef_scale", 0.3, 3.0)
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256, 512]),
            "ent_coef": f"auto_{ent_coef_scale}",
            "tau": trial.suggest_float("tau", 0.001, 0.02, log=True),
            "train_freq": trial.suggest_categorical("train_freq", [1, 2, 4, 8]),
            "gradient_steps": trial.suggest_categorical("gradient_steps", [1, 2, 4, 8]),
            "target_update_interval": trial.suggest_categorical(
                "target_update_interval", [1, 5, 10]
            ),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> SACController:
        return SACController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the SAC controller.")

        config = load_rl_controller_config(self.config_path)

        # This controller relies on a continuous action space.
        config.environment_wrapper.discrete_action = False
        config.environment_wrapper.continuous_action = True

        env_wrap_manager = EnvWrapperManager([], config.environment_wrapper)

        hp = config.hyperparameters

        if config.hyperparameter_tuning is not None and config.hyperparameter_tuning.enabled:
            hp = tune_hp(
                self,
                hp_tuning_config=config.hyperparameter_tuning,
                env_wrapper_manager=env_wrap_manager,
                is_env_adapter=False,
                hp=config.hyperparameters,
            )

        return super().create_rl_controller_setup(hp, env_wrap_manager)
