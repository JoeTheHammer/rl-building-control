from typing import Any, Dict, Optional

import gymnasium as gym
import optuna
from gymnasium import Env
from stable_baselines3 import DQN

from controllers.base_controller import ControllerSetup
from controllers.base_rl_controller import (
    IRLController,
    IRLControllerFactory,
    load_rl_controller_config,
)
from environments.base_factory import IEnvironmentFactory


class DQNController(IRLController):
    """
    Controller for the Deep Q-Network (DQN) algorithm.
    This implementation uses the Stable-Baselines3 DQN, which includes
    improvements from Double DQN (DDQN) by default to prevent overestimation.
    """

    def __init__(self, env: gym.Env, params: Dict):
        """
        Initializes the DQN model with the given environment and parameters.
        DQN is a value-based, off-policy algorithm suitable for discrete action spaces.
        """
        super().__init__(env)
        self.model = DQN("MlpPolicy", env, **params)

    def get_action(self, state: Any) -> Any:
        """
        Predicts the deterministic action to take given the current state.
        For DQN, the action is chosen greedily with respect to the learned Q-values.
        """
        action, _ = self.model.predict(state, deterministic=True)
        return action

    def train(self, timesteps: int):
        """
        Trains the DQN model for a specified number of timesteps.
        """
        self.model.learn(total_timesteps=timesteps, log_interval=1)


class DQNFactory(IRLControllerFactory):
    """
    Factory for the DQNController, including hyperparameter tuning with Optuna.
    This class suggests and builds a DQN controller with appropriate parameters.
    """

    def _suggest_hyperparameters_space(
        self, trial: Optional[optuna.Trial] = None
    ) -> Dict[str, Any]:
        """
        Suggests hyperparameters for DQN, either returning defaults or using Optuna.
        Key parameters for DQN include epsilon-greedy exploration settings and
        target network update frequency.
        """
        if trial is None:
            # Return default values for DQN if no Optuna trial is provided.
            # These values are based on the stable-baselines3 DQN defaults.
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "buffer_size": 100000,
                "learning_starts": 50000,
                "batch_size": 32,
                "target_update_interval": 1000,
                "exploration_fraction": 0.1,
                "exploration_final_eps": 0.05,
            }

        # Suggest a search space for Optuna.
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "buffer_size": trial.suggest_int("buffer_size", 10000, 500000, step=10000),
            "learning_starts": trial.suggest_int("learning_starts", 10000, 100000),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128, 256]),
            "target_update_interval": trial.suggest_int("target_update_interval", 100, 5000),
            "exploration_fraction": trial.suggest_float("exploration_fraction", 0.05, 0.5),
            "exploration_final_eps": trial.suggest_float("exploration_final_eps", 0.01, 0.1),
        }

    def _build_controller(self, env: Env, hyper_params: Dict, **kwargs) -> DQNController:
        """
        Builds and returns a new DQNController instance.
        """
        return DQNController(env, hyper_params)

    def create_controller_setup(self) -> ControllerSetup:
        """
        Creates the DQN controller setup, loading configuration and environment.
        This method is the entry point for setting up the controller.
        """
        if self.config_path is None or self.config_path == "":
            raise RuntimeError("No configuration was provided for the DQN controller.")

        config = load_rl_controller_config(self.config_path)

        return super().create_rl_controller_setup(
            is_discrete_action_space=True,
            normalize_state=config.environment_wrapper.normalize_state,
        )
