from typing import Dict
from gymnasium import Env
from stable_baselines3 import PPO

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLControllerFactory,
    load_rl_controller_config,
)
from controllers.utils import add_squash_output_to_hp, stabilize_training
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager


class PPOFactory(IRLControllerFactory):

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        # Add this to ensure that output of controller is in defined (tanh) range.

        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

        return OnPolicyAdapter(
            env=env,
            model_class=PPO,
            hyper_params=hyper_params,
            policy="MlpPolicy",
        )

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)
        env_wrap_manager = EnvWrapperManager(
            [ContinuousActionWrapper], rl_config.environment_wrapper
        )
        hp = rl_config.hyperparameters

        return super().create_rl_controller_setup_new(hp, env_wrap_manager, is_env_adapter=True)
