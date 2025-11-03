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
    """Run Optuna-based hyperparameter tuning with the sampler defined in HyperparameterTuning config."""

    sampler_map = {
        "tpe": optuna.samplers.TPESampler,
        "random": optuna.samplers.RandomSampler,
        "grid": optuna.samplers.GridSampler,  # requires search_space
        "cmaes": optuna.samplers.CmaEsSampler,
        "nsgaii": optuna.samplers.NSGAIISampler,
    }

    sampler_name = (hp_tuning_config.sampler or "tpe").lower()
    sampler_cls = sampler_map.get(sampler_name, optuna.samplers.TPESampler)

    if sampler_cls is optuna.samplers.GridSampler:
        if not hasattr(controller_factory, "get_grid_search_space"):
            raise ValueError(
                "Controller factory must implement get_grid_search_space() " "to use GridSampler."
            )
        search_space = controller_factory.get_grid_search_space()
        sampler = optuna.samplers.GridSampler(search_space)
    else:
        sampler = sampler_cls()

    logger.info(f"Using Optuna sampler: {sampler_cls.__name__}")

    def objective(trial: optuna.Trial) -> float:
        trial_hp = _suggest_hyperparameters(controller_factory, trial, hp)

        # Needed to keep n_steps and batch_size compatible in PPO controller
        if "nstep_batch" in trial_hp:
            trial_hp.update(trial_hp.pop("nstep_batch"))

        logger.info(f"Test with these hp: {trial_hp}")

        env_t = controller_factory.env_factory.create_environment()
        env_t = env_wrapper_manager.apply_wrappers(env_t)
        ctrl = controller_factory.build_controller(env_t, trial_hp)

        logger.info(f"Training for {hp_tuning_config.training_timesteps} timesteps")
        ctrl.train(hp_tuning_config.training_timesteps)

        if is_env_adapter:
            # If OnPolicyAdapter is returned, it serves as controller and env
            env_t = ctrl

        rewards = Experiment(
            name="hyperparameter_tuning",
            env=env_t,
            controller=ctrl,
            experiment_id=0,
            episodes=hp_tuning_config.num_episodes,
            status_tracking=False,
        ).run()

        env_t.close()
        return float(np.mean(rewards))

    set_hyperparameter_tuning_status()
    study = optuna.create_study(direction="maximize", sampler=sampler)

    logger.info("Starting hyperparameter tuning.")
    study.optimize(objective, n_trials=hp_tuning_config.num_trials)

    logger.info(f"Best trial params: {study.best_params}")
    logger.info(f"Best value: {study.best_value:.4f}")

    best_params = dict(study.best_params)
    if "ent_coef_scale" in best_params:
        best_params["ent_coef"] = f"auto_{best_params.pop('ent_coef_scale')}"

    return {**best_params, **hp}
