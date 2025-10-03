from typing import Dict, Any, Optional

import numpy as np
import optuna

from controllers.base_hp_tunable_controller import IHPTunableControllerFactory
from controllers.config import HyperparameterTuning
from custom_loggers.setup_logger import logger
from experiment.experiment import Experiment
from experiment.status import set_hyperparameter_tuning_status
from wrappers.manager import EnvWrapperManager


def _suggest_hyperparameters(
    controller_factory: IHPTunableControllerFactory,
    trial: Optional[optuna.Trial] = None,
    fixed_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    fixed_params = fixed_params or {}

    # First suggest everything using Optuna
    suggested = controller_factory.suggest_hyperparameters_space(trial)

    # Then override with anything the user has fixed
    return {**suggested, **fixed_params}


def tune_hp(
    controller_factory: IHPTunableControllerFactory,
    hp_tuning_config: HyperparameterTuning,
    env_wrapper_manager: EnvWrapperManager,
    hp: Dict[str, Any],
    is_env_adapter: bool = False,
) -> Dict[str, Any]:
    def objective(trial: optuna.Trial) -> float:
        trial_hp = _suggest_hyperparameters(controller_factory, trial, hp)

        logger.info(f"Test with these hp: {trial_hp}")

        env_t = controller_factory.env_factory.create_environment()
        env_t = env_wrapper_manager.apply_wrappers(env_t)

        ctrl = controller_factory.build_controller(env_t, trial_hp)

        if is_env_adapter:
            # If on policy adapter is returned by build_controller that serves as controller and env.
            env_t = ctrl

        rewards = Experiment(
            name="hyperparameter_tuning",
            env=env_t,
            controller=ctrl,
            episodes=hp_tuning_config.num_episodes,
            status_tracking=False,
        ).run()
        env_t.close()
        return float(np.mean(rewards))

    set_hyperparameter_tuning_status()
    study = optuna.create_study(direction="maximize")
    logger.info("Starting hyperparameter tuning.")
    study.optimize(objective, n_trials=hp_tuning_config.num_trials)
    return {**study.best_params, **hp}
