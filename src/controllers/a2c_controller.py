from typing import Any, Dict, Optional

import optuna
from gymnasium import Env
from stable_baselines3 import A2C

from adapters.on_policy_vec_env import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLControllerFactory,
)
from controllers.utils import add_squash_output_to_hp


class A2CFactory(IRLControllerFactory):

    def _suggest_hyperparameters_space(
            self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:
        """
        Suggests a set of hyperparameters for the PPO algorithm.
        Provides stable defaults if no Optuna trial is given.
        """
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

        normalize_reward = kwargs.get("normalize_reward", False)
        report_denormalized_state = kwargs.get("report_denormalized_state", False)

        return OnPolicyAdapter(
            env=env,
            model_class=A2C,
            hyperparams=hyper_params,
            normalize_reward=normalize_reward,
            report_denormalized_state=report_denormalized_state,
            normalize_action=False,
            policy="MlpPolicy",
        )

    def create_controller_setup(self) -> ControllerSetup:

        if self.config_path is None:
            raise RuntimeError("No configuration was provided for the PPO controller.")

        return super().create_rl_controller_setup(
            is_continuous_action_space=True,
            on_policy=True,
            normalize_reward=False,
        )
