from typing import Any, Dict, Optional

import optuna
from gymnasium import Env
from stable_baselines3 import PPO

from adapters.on_policy_vec_env import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLControllerFactory,
    load_rl_controller_config,
)
from controllers.utils import add_squash_output_to_hp, stabilize_training
from environments.base_factory import IEnvironmentFactory


class PPOFactory(IRLControllerFactory):

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
                "learning_rate": 3e-4,
                "n_steps": 2048,
                "batch_size": 64,
                "n_epochs": 10,
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "clip_range": 0.2,
                "ent_coef": 0.0,
                "vf_coef": 0.5,
            }

        # Use Optuna to suggest a range of values for tuning
        return {
            "n_steps": trial.suggest_categorical("n_steps", [512, 1024, 2048]),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999, log=True),
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "clip_range": trial.suggest_categorical("clip_range", [0.1, 0.2, 0.3]),
            "n_epochs": trial.suggest_categorical("n_epochs", [5, 10, 20]),
            "gae_lambda": trial.suggest_float("gae_lambda", 0.9, 1.0),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256]),
            "vf_coef": trial.suggest_float("vf_coef", 0.1, 1.0),
            "ent_coef": trial.suggest_float("ent_coef", 0.0, 0.1),
        }

    def _build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        # Add this to ensure that output of controller is in defined (tanh) range.

        hyper_params = add_squash_output_to_hp(hyper_params)
        hyper_params = stabilize_training(hyper_params)

        normalize_reward = kwargs.get("normalize_reward", False)
        report_denormalized_state = kwargs.get("report_denormalized_state", False)

        return OnPolicyAdapter(
            env=env,
            model_class=PPO,
            hyperparams=hyper_params,
            normalize_reward=normalize_reward,
            report_denormalized_state=report_denormalized_state,
            policy="MlpPolicy",
        )

    def create_controller_setup(
        self,
        config_path: str | None = None,
        environment_factory: IEnvironmentFactory | None = None,
    ) -> ControllerSetup:

        if config_path is None:
            raise RuntimeError("No configuration was provided for the PPO controller.")

        config = load_rl_controller_config(config_path)

        return super().create_rl_controller_setup(
            config=config,
            environment_factory=environment_factory,
            is_continuous_action_space=True,
            on_policy=True,
            normalize_reward=False,
        )
