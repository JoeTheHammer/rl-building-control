from typing import Any, Dict, Optional

import optuna
from gymnasium import Env
from stable_baselines3 import A2C

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import IHPTunableControllerFactory
from controllers.base_rl_controller import load_rl_controller_config
from controllers.utils import add_squash_output_to_hp
from tuning.hp_tuning import tune_hp
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager


class A2CFactory(IHPTunableControllerFactory):
    """
    Factory for the DDPGController, including hyperparameter tuning with Optuna.
    """

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        if trial is None:
            # Return a robust set of default values
            return {
                "learning_rate": 7e-4,
                "gamma": 0.99,
                "ent_coef": 0.1,
                "vf_coef": 0.5,
            }

        # Use Optuna to suggest a range of values for tuning
        return {
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999, log=True),
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "vf_coef": trial.suggest_float("vf_coef", 0.1, 1.0),
            "ent_coef": trial.suggest_float("ent_coef", 0.0, 0.1),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:

        # Add this to ensure that output of controller is in defined (tanh) range.
        hyper_params = add_squash_output_to_hp(hyper_params)

        return OnPolicyAdapter(
            env=env,
            model_class=A2C,
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
        hp_tuning_config = rl_config.hyperparameter_tuning

        if hp_tuning_config is not None and hp_tuning_config.enabled:
            # This controller supports hp tuning so we can use if.
            hp = tune_hp(self, hp_tuning_config, env_wrap_manager, hp, is_env_adapter=True)

        return super().create_rl_controller_setup_new(hp, env_wrap_manager, is_env_adapter=True)
