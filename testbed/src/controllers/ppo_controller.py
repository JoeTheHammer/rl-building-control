from typing import Dict, List, Type
import gymnasium as gym
from gymnasium import Env
from sinergym.utils.wrappers import NormalizeAction
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

    def __init__(self):
        super().__init__()
        self.normalize_reward = None

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        # Add this to ensure that output of controller is in defined (tanh) range.

        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

        return OnPolicyAdapter(
            env=env,
            model_class=PPO,
            hyper_params=hyper_params,
            policy="MlpPolicy",
            normalize_reward=self.normalize_reward,
        )

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)

        wrapper_classes: List[Type[gym.Wrapper]] = [ContinuousActionWrapper]

        if rl_config.environment_wrapper.normalize_action:
            wrapper_classes.append(NormalizeAction)

        self.normalize_reward = rl_config.environment_wrapper.normalize_reward

        env_wrap_manager = EnvWrapperManager(wrapper_classes)
        hp = rl_config.hyperparameters

        return super().create_rl_controller_setup(hp, env_wrap_manager, is_env_adapter=True)
