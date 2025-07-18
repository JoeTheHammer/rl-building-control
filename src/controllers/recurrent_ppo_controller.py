from typing import (
    Any,
    Dict,
)

import gymnasium as gym
from sb3_contrib import RecurrentPPO
from sinergym.utils.wrappers import NormalizeAction
from stable_baselines3.common.monitor import Monitor

from adapters.on_policy_vec_env import OnPolicyAdapter
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

        env = Monitor(env)

        self.model = RecurrentPPO(
            "MlpLstmPolicy",
            env,
            verbose=0,
            use_sde=True,
            policy_kwargs=dict(squash_output=True),
            **params,
        )

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def train(self, timesteps: int):
        self.model.learn(timesteps)


class RecurrentPPOProvider(IRLControllerProvider):

    def _build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:

        env = Monitor(env)

        if "policy_kwargs" not in hyper_params:
            hyper_params["policy_kwargs"] = {}
        hyper_params["policy_kwargs"]["squash_output"] = True
        hyper_params["use_sde"] = True
        normalize_reward = kwargs.get("normalize_reward", False)
        report_denormalized_state = kwargs.get("report_denormalized_state", False)
        return OnPolicyAdapter(
            env=env,
            model_class=RecurrentPPO,
            hyperparams=hyper_params,
            normalize_reward=normalize_reward,
            report_denormalized_state=report_denormalized_state,
            normalize_action=True,
            policy="MlpLstmPolicy",
        )
        # return PPOController(env, hyper_params)

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
            on_policy=True,
        )
