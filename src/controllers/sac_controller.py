from typing import Any, Dict

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import SAC

from controllers.base_rl_controller import IRLControllerProvider, IRLController
from environments.base_provider import IEnvironmentProvider


class SACController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)
        self.model = SAC(
            "MlpPolicy",
            self.env,
            learning_rate=params["learning_rate"],
            gamma=params["gamma"],
            ent_coef=params["ent_coef"],
            batch_size=params["batch_size"],
            verbose=0,
        )

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        self.model.learn(timesteps)


class SACProvider(IRLControllerProvider):
    def _build_controller(self, env: Env, hyper_params: Dict) -> SACController:
        return SACController(env, hyper_params)

    def _suggest_hyperparameters(self, trial: optuna.Trial) -> Dict:
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "ent_coef": trial.suggest_float("ent_coef", 1e-8, 1e-1),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
        }

    def create_controller(
        self,
        env: gym.Env,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
        train_timesteps: int = 1000,
        is_continuous_action_space: bool = False,
    ) -> IRLController:

        # Implementation of this method needed to set continuous action space to true
        return super().create_controller(
            env, config_path, environment_provider, environment_config, train_timesteps, True
        )
