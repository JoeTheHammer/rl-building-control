from typing import Any, Dict, Optional, List, Type

import gymnasium
import optuna
from gymnasium import Env
from sinergym.utils.wrappers import NormalizeAction
from stable_baselines3 import PPO

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import IHPTunableControllerFactory
from controllers.base_rl_controller import load_rl_controller_config
from controllers.utils import add_squash_output_to_hp, stabilize_training
from tuning.hp_tuning import tune_hp
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager


class PPOFactory(IHPTunableControllerFactory):
    """Factory for the PPO controller, including Optuna-based hyperparameter tuning."""

    def __init__(self):
        super().__init__()
        self.normalize_reward = None

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        # define valid combinations as tuples
        nstep_batch_pairs = [
            {"n_steps": 2048, "batch_size": 128},
            {"n_steps": 4096, "batch_size": 256},
            {"n_steps": 8192, "batch_size": 512},
        ]

        return {
            "learning_rate": [1e-5, 1e-4, 5e-4],
            "gamma": [0.95, 0.99],
            "gae_lambda": [0.9, 0.95],
            "ent_coef": [0.0, 0.01, 0.02],
            "vf_coef": [0.3, 0.5],
            "clip_range": [0.1, 0.2],
            "target_kl": [0.005, 0.01],
            "max_grad_norm": [0.5],
            # include the joint parameter space
            "nstep_batch": nstep_batch_pairs,
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        if trial is None:
            return {
                "learning_rate": 0.0004,
                "n_steps": 4096,
                "gamma": 0.995,
                "gae_lambda": 0.95,
                "vf_coef": 0.5,
                "target_kl": 0.01,
                "ent_coef": 0.015,
                "clip_range": 0.2,
                "batch_size": 512,
                "max_grad_norm": 0.5,
            }

        # Choose n_steps first
        n_steps = trial.suggest_categorical("n_steps", [2048, 4096, 8192])
        # Then ensure batch_size divides n_steps
        possible_batches = [b for b in [128, 256, 512, 1024] if n_steps % b == 0]
        batch_size = trial.suggest_categorical("batch_size", possible_batches)

        return {
            "n_steps": n_steps,
            "batch_size": batch_size,
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999, log=True),
            "gae_lambda": trial.suggest_float("gae_lambda", 0.8, 0.98),
            "ent_coef": trial.suggest_float("ent_coef", 0.0, 0.05),
            "vf_coef": trial.suggest_float("vf_coef", 0.3, 0.8),
            "clip_range": trial.suggest_float("clip_range", 0.1, 0.3),
            "target_kl": trial.suggest_float("target_kl", 0.002, 0.02, log=True),
            "max_grad_norm": trial.suggest_float("max_grad_norm", 0.3, 1.0),
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
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
        if not self.config_path:
            raise RuntimeError("No configuration provided for the PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)
        wrapper_classes: List[Type[gymnasium.Wrapper]] = [ContinuousActionWrapper]

        if rl_config.environment_wrapper.normalize_action:
            wrapper_classes.append(NormalizeAction)

        self.normalize_reward = rl_config.environment_wrapper.normalize_reward
        env_wrap_manager = EnvWrapperManager(wrapper_classes)

        hp = rl_config.hyperparameters
        hp_tuning_config = rl_config.hyperparameter_tuning

        # enable Optuna tuning
        if hp_tuning_config is not None and hp_tuning_config.enabled:
            hp = tune_hp(self, hp_tuning_config, env_wrap_manager, hp, is_env_adapter=True)

        return super().create_rl_controller_setup(hp, env_wrap_manager, is_env_adapter=True)
