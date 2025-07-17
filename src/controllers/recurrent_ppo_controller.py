from typing import (
    Any,
    Dict,
)

import gymnasium as gym
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.monitor import Monitor

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerProvider,
    load_rl_controller_config,
)
from environments.base_provider import IEnvironmentProvider


class PPOController(IRLController):

    def __init__(self, env: gym.Env, params: Dict):
        super().__init__(env)

        monitored_env = Monitor(self.env)

        self.model = RecurrentPPO(
            "MlpLstmPolicy",
            monitored_env,
            verbose=0,
            **params,
        )

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        self.model.learn(timesteps)


class RecurrentPPOProvider(IRLControllerProvider):

    def _build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> PPOController:
        return PPOController(env, hyper_params)

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> ControllerSetup:

        if config_path is None:
            raise RuntimeError("No configuration was provided for the PPO controller.")

        config = load_rl_controller_config(config_path)

        return super().create_rl_controller_setup(
            config=config,
            environment_provider=environment_provider,
            environment_config=environment_config,
            is_continuous_action_space=True,
            normalize_state=True,
        )
