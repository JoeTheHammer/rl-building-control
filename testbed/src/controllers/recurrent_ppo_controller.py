from typing import (
    Dict,
)

import gymnasium as gym
from sb3_contrib import RecurrentPPO

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLControllerFactory,
    load_rl_controller_config,
)
from controllers.utils import add_squash_output_to_hp, stabilize_training
from wrappers.manager import EnvWrapperManager
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from sinergym.utils.wrappers import NormalizeAction


class RecurrentPPOFactory(IRLControllerFactory):

    def build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

        return OnPolicyAdapter(
            env=env,
            model_class=RecurrentPPO,
            hyper_params=hyper_params,
            policy="MlpLstmPolicy",
        )

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)
        env_wrap_manager = EnvWrapperManager(
            [ContinuousActionWrapper, NormalizeAction], rl_config.environment_wrapper
        )
        hp = rl_config.hyperparameters

        return super().create_rl_controller_setup_new(hp, env_wrap_manager, is_env_adapter=True)
