from typing import Any, Dict

import gymnasium as gym
import optuna
from stable_baselines3 import SAC

from controllers.base_controller import IController
from controllers.controller_provider import IControllerProvider
from custom_loggers.setup_logger import logger
from environments.base_provider import IEnvironmentProvider
from experiment.experiment import Experiment


class SACController(IController):

    def __init__(self, env: gym.Env, **hp):
        super().__init__(env)
        self._hp = hp
        self._build_model()

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action

    def apply_hyperparameters(self, new_hp: Dict):
        self._hp.update(new_hp)
        self._build_model()

    def _build_model(self):
        self.model = SAC(
            "MlpPolicy",
            self.env,
            learning_rate=self._hp["learning_rate"],
            gamma=self._hp["gamma"],
            ent_coef=self._hp["ent_coef"],
            batch_size=self._hp["batch_size"],
            verbose=0,
        )


def _build_controller(env, hyperparams):
    # Communicate to env that SAC support only continuous action space.

    # Merge with some defaults:
    defaults = {
        "learning_rate": 3e-4,
        "gamma": 0.99,
        "ent_coef": 0.1,
        "batch_size": 64,
    }
    merged = {**defaults, **hyperparams}
    return SACController(env, **merged)


def _suggest_hyperparameters(trial):
    return {
        "learning_rate": trial.suggest_loguniform("learning_rate", 1e-5, 1e-3),
        "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
        "ent_coef": trial.suggest_loguniform("ent_coef", 1e-8, 1e-1),
        "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
    }


def _tune_hyperparameters(
    env_provider: IEnvironmentProvider, env_config: str, num_trials: int, trial_episodes: int
) -> Dict[str, Any]:
    def objective(trial: optuna.Trial) -> float:
        # ① Sample a fresh set of hyperparams
        trial_hp = _suggest_hyperparameters(trial)

        # ② Build a brand-new env & controller per trial
        env_t = env_provider.create_environment(env_config)
        env_t.continuous_action_space = True
        ctrl = _build_controller(env_t, {})  # start from defaults
        ctrl.apply_hyperparameters(trial_hp)

        # ③ Evaluate with a short experiment
        return Experiment(name="optuna", env=env_t, controller=ctrl).run()

    study = optuna.create_study(direction="maximize")

    logger.info("Starting hyperparameter tuning.")

    study.optimize(objective, n_trials=num_trials)
    return study.best_params


class SACProvider(IControllerProvider):
    def create_controller(
        self,
        env: gym.Env,
        config_path: str | None = None,
        environment_provider: IEnvironmentProvider | None = None,
        environment_config: str | None = None,
    ) -> SACController:
        env.continuous_action_space = True
        controller = _build_controller(env, {})

        best_hp = _tune_hyperparameters(environment_provider, environment_config, 2, 50)
        logger.info("Ended hyperparameter tuning.")
        logger.info(f"Best hyperparameters: {best_hp}")

        controller.apply_hyperparameters(best_hp)

        # Real training
        controller.model.learn(2000)

        return controller
