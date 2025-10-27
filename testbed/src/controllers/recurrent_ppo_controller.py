from typing import (
    Dict,
    Type,
    List,
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
from custom_loggers.setup_logger import logger


class RecurrentPPOFactory(IRLControllerFactory):

    def __init__(self):
        super().__init__()
        self.normalize_reward = False

    def build_controller(self, env: gym.Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

        return OnPolicyAdapter(
            env=env,
            model_class=RecurrentPPO,
            hyper_params=hyper_params,
            policy="MlpLstmPolicy",
            normalize_reward=self.normalize_reward,
        )

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)

        if rl_config.hyperparameter_tuning.enabled:
            logger.warning("The Recurrent PPO controller does not support hyperparameter tuning.")

        wrapper_classes: List[Type[gym.Wrapper]] = [ContinuousActionWrapper]

        if rl_config.environment_wrapper.normalize_action:
            wrapper_classes.append(NormalizeAction)

        self.normalize_reward = rl_config.environment_wrapper.normalize_reward

        env_wrap_manager = EnvWrapperManager(wrapper_classes)
        hp = rl_config.hyperparameters

        return super().create_rl_controller_setup(hp, env_wrap_manager, is_env_adapter=True)
