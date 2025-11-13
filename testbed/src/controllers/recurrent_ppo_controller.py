from typing import Any, Dict, Optional, List, Type

import gymnasium as gym
import optuna
from gymnasium import Env
from sinergym.utils.wrappers import NormalizeAction
from sb3_contrib import RecurrentPPO

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import IHPTunableControllerFactory
from controllers.base_rl_controller import load_rl_controller_config
from controllers.utils import add_squash_output_to_hp, stabilize_training
from tuning.hp_tuning import tune_hp
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager
from custom_loggers.setup_logger import logger


class RecurrentPPOFactory(IHPTunableControllerFactory):
    """
    Factory for Recurrent PPO with Optuna-based hyperparameter tuning.
    """

    def __init__(self):
        super().__init__()
        self.normalize_reward = False

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        # Valid pairs (n_steps, batch_size must divide n_steps!)
        nstep_batch_pairs = [
            {"n_steps": 1024, "batch_size": 64},
            {"n_steps": 2048, "batch_size": 128},
            {"n_steps": 4096, "batch_size": 256},
        ]

        return {
            "learning_rate": [1e-5, 5e-5, 1e-4, 3e-4],
            "gamma": [0.98, 0.99, 0.995],
            "gae_lambda": [0.9, 0.95, 0.98],
            "ent_coef": [0.0, 0.001, 0.01],
            "vf_coef": [0.3, 0.5, 0.7],
            "clip_range": [0.1, 0.2, 0.3],
            "target_kl": [0.005, 0.01],
            "max_grad_norm": [0.3, 0.5, 0.7],
            "n_epochs": [5, 10, 15],
            "nstep_batch": nstep_batch_pairs,
        }

    def suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:

        if trial is None:
            return {
                "learning_rate": 1e-5,
                "n_steps": 2048,
                "batch_size": 64,
                "n_epochs": 10,
                "gamma": 0.995,
                "gae_lambda": 0.95,
                "clip_range": 0.2,
                "vf_coef": 0.5,
                "ent_coef": 0.001,
                "max_grad_norm": 0.5,
                "target_kl": None,
            }

        # Key constraint:
        # batch_size must divide n_steps
        n_steps = trial.suggest_categorical("n_steps", [1024, 2048, 4096, 8192])
        possible_batch_sizes = [b for b in [32, 64, 128, 256, 512] if n_steps % b == 0]
        batch_size = trial.suggest_categorical("batch_size", possible_batch_sizes)

        return {
            "n_steps": n_steps,
            "batch_size": batch_size,

            "learning_rate": trial.suggest_float("learning_rate", 1e-6, 1e-3, log=True),
            "n_epochs": trial.suggest_int("n_epochs", 5, 20),
            "gamma": trial.suggest_float("gamma", 0.90, 0.999, log=True),
            "gae_lambda": trial.suggest_float("gae_lambda", 0.85, 0.98),
            "clip_range": trial.suggest_float("clip_range", 0.1, 0.3),
            "vf_coef": trial.suggest_float("vf_coef", 0.3, 0.8),
            "ent_coef": trial.suggest_float("ent_coef", 0.0, 0.02),
            "max_grad_norm": trial.suggest_float("max_grad_norm", 0.3, 1.0),
            "target_kl": trial.suggest_float("target_kl", 0.002, 0.02, log=True),
        }

    # -------------------------------------------------------------
    # Build Controller
    # -------------------------------------------------------------
    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        # Important: apply your stabilizers
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
        if not self.config_path:
            raise RuntimeError("No configuration provided for the Recurrent PPO controller.")

        rl_config = load_rl_controller_config(self.config_path)

        wrapper_classes: List[Type[gym.Wrapper]] = [ContinuousActionWrapper]

        if rl_config.environment_wrapper.normalize_action:
            wrapper_classes.append(NormalizeAction)

        self.normalize_reward = rl_config.environment_wrapper.normalize_reward

        env_wrap_manager = EnvWrapperManager(wrapper_classes)

        hp = rl_config.hyperparameters
        hp_tuning_config = rl_config.hyperparameter_tuning

        # Enable Optuna/grid tuning
        if hp_tuning_config is not None and hp_tuning_config.enabled:
            logger.info("Starting Recurrent PPO hyperparameter tuning...")
            hp = tune_hp(
                self,
                hp_tuning_config,
                env_wrap_manager,
                hp,
                is_env_adapter=True,
            )
            logger.info(f"Finished Recurrent PPO tuning. Best HP: {hp}")

        return super().create_rl_controller_setup(hp, env_wrap_manager, is_env_adapter=True)
