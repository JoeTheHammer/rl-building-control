from typing import Any, Dict, Optional, List, Type

import gymnasium
import optuna
from gymnasium import Env
from sinergym.utils.wrappers import NormalizeAction
from stable_baselines3 import A2C

from adapters.on_policy_adapter import OnPolicyAdapter
from controllers.base_controller import ControllerSetup
from controllers.base_hp_tunable_controller import HPTunableControllerFactory
from controllers.base_rl_controller import load_rl_controller_config
from tuning.hp_tuning import tune_hp
from wrappers.continuous_action_wrapper import ContinuousActionWrapper
from wrappers.manager import EnvWrapperManager


class A2CFactory(HPTunableControllerFactory):
    """
    Factory for the A2C controller, including hyperparameter tuning with Optuna.
    """

    def __init__(self):
        super().__init__()
        self.normalize_reward = None

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        """
        Discrete grid for quick sanity checks.
        Focus: the few knobs that usually move the needle most.
        """
        return {
            # Core learning dynamics
            "learning_rate": [1e-5, 3e-5, 1e-4, 3e-4, 7e-4, 1e-3],
            "gamma": [0.90, 0.95, 0.97, 0.99, 0.995],
            "gae_lambda": [0.80, 0.90, 0.95, 1.00],
            "n_steps": [5, 16, 32, 64, 128, 256],
            # Exploration / regularization
            "ent_coef": [0.0, 0.001, 0.005, 0.01, 0.02, 0.05],
            "normalize_advantage": [False, True],
            # Value vs policy balance + stability
            "vf_coef": [0.2, 0.5, 0.8, 1.0],
            "max_grad_norm": [0.25, 0.5, 1.0, 2.0],
            # Optimizer choice (A2C classic: RMSProp)
            "use_rms_prop": [True, False],
            "rms_prop_eps": [1e-6, 1e-5, 1e-4],
            # gSDE exploration (only meaningful in continuous action spaces)
            "use_sde": [False, True],
            "sde_sample_freq": [-1, 16, 32, 64],
        }

    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        if trial is None:
            # Robust defaults (SB3-like, plus a bit of entropy if you want exploration by default)
            return {
                "learning_rate": 7e-4,
                "n_steps": 32,
                "gamma": 0.99,
                "gae_lambda": 1.0,
                "ent_coef": 0.01,
                "vf_coef": 0.5,
                "max_grad_norm": 0.5,
                "use_rms_prop": True,
                "rms_prop_eps": 1e-5,
                "normalize_advantage": False,
                "use_sde": False,
                "sde_sample_freq": -1,
            }

        # --- Core learning dynamics ---
        learning_rate = trial.suggest_float("learning_rate", 1e-5, 3e-3, log=True)
        gamma = trial.suggest_float("gamma", 0.90, 0.9999, log=True)
        gae_lambda = trial.suggest_float("gae_lambda", 0.80, 1.00)
        n_steps = trial.suggest_int("n_steps", 8, 512, log=True)

        # --- Exploration / regularization ---
        ent_coef = trial.suggest_float("ent_coef", 0.0, 0.05)
        normalize_advantage = trial.suggest_categorical("normalize_advantage", [False, True])

        # --- Value vs policy balance + stability ---
        vf_coef = trial.suggest_float("vf_coef", 0.1, 1.5)
        max_grad_norm = trial.suggest_float("max_grad_norm", 0.1, 5.0, log=True)

        # --- Optimizer knobs ---
        use_rms_prop = trial.suggest_categorical("use_rms_prop", [True, False])
        rms_prop_eps = trial.suggest_float("rms_prop_eps", 1e-6, 1e-4, log=True)

        # --- gSDE exploration (continuous only; harmless to suggest, but only matters for Box) ---
        use_sde = trial.suggest_categorical("use_sde", [False, True])
        # If gSDE is off, keep default -1 to avoid pointless churn
        sde_sample_freq = (
            trial.suggest_categorical("sde_sample_freq", [-1, 8, 16, 32, 64, 128])
            if use_sde
            else -1
        )

        return {
            "learning_rate": learning_rate,
            "n_steps": n_steps,
            "gamma": gamma,
            "gae_lambda": gae_lambda,
            "ent_coef": ent_coef,
            "vf_coef": vf_coef,
            "max_grad_norm": max_grad_norm,
            "use_rms_prop": use_rms_prop,
            "rms_prop_eps": rms_prop_eps,
            "normalize_advantage": normalize_advantage,
            "use_sde": use_sde,
            "sde_sample_freq": sde_sample_freq,
        }

    def build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> OnPolicyAdapter:
        return OnPolicyAdapter(
            env=env,
            model_class=A2C,
            hyper_params=hyper_params,
            policy="MlpPolicy",
        )

    def create_controller_setup(self) -> ControllerSetup:
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the A2C controller.")

        rl_config = load_rl_controller_config(self.config_path)

        wrapper_classes: List[Type[gymnasium.Wrapper]] = [ContinuousActionWrapper]

        if rl_config.environment_wrapper.normalize_action:
            wrapper_classes.append(NormalizeAction)

        self.normalize_reward = rl_config.environment_wrapper.normalize_reward

        env_wrap_manager = EnvWrapperManager(wrapper_classes)

        hp = rl_config.hyperparameters
        hp_tuning_config = rl_config.hyperparameter_tuning

        if hp_tuning_config is not None and hp_tuning_config.enabled:
            hp = tune_hp(self, hp_tuning_config, env_wrap_manager, hp, is_env_adapter=True)

        return super().create_rl_controller_setup(hp, env_wrap_manager, is_adapter=True)
