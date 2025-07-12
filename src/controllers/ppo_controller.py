from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import PPO

from controllers.base_controller import IController
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerProvider,
    load_rl_controller_config,
)
from environments.base_provider import IEnvironmentProvider


class PPOController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)
        self.model = PPO(policy="MlpPolicy", env=self.env, learning_rate=params["learning_rate"])

    def train(self, timesteps: int):
        self.model.learn(timesteps)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action


class PPOProvider(IRLControllerProvider):

    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:

        if trial is None:
            return {"learning_rate": 3e-4}

        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3),
        }

    def _build_controller(self, env: Env, hyper_params: Dict) -> IRLController:
        return PPOController(env, hyper_params)

    def create_controller(
        self,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> IController:

        if config_path is None:
            raise RuntimeError("No configuration was provided for the PPO controller.")


        config = load_rl_controller_config(config_path)

        return super().create_rl_controller(
            config=config,
            environment_provider=environment_provider,
            environment_config=environment_config,
            is_continuous_action_space=True,
            normalize_observation=True
        )
