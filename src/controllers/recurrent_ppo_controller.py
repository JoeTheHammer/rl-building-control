from typing import (
    Any,
    Dict,
)

import gymnasium as gym
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.monitor import Monitor

from adapters.on_policy_vec_env import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from controllers.utils import add_squash_output_to_hp, stabilize_training
from environments.base_factory import IEnvironmentFactory


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


class RecurrentPPOFactory(IRLControllerFactory):

    def _build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:

        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

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

    def create_controller_setup(self) -> ControllerSetup:

        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the PPO controller.")

        return super().create_rl_controller_setup(
            is_continuous_action_space=True,
            on_policy=True,
        )
