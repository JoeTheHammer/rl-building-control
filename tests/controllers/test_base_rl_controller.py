from typing import Any, Dict
from unittest.mock import Mock

import gymnasium
import optuna
import pytest
from gymnasium import Env

from controllers.base_rl_controller import IRLController, IRLControllerProvider
from environments.base_provider import IEnvironmentProvider

# ---- Dummy Test Implementation ----


class DummyController(IRLController):
    def train(self, timesteps: int):
        self.trained_timesteps = timesteps

    def get_action(self, state: Any) -> Any:
        return 0


class DummyRLControllerProvider(IRLControllerProvider):
    def _build_controller(self, env: Env, hyper_params: Dict) -> IRLController:
        ctrl = DummyController(env)
        ctrl.hp = hyper_params
        return ctrl

    def _suggest_hyperparameters_space(self, trial: optuna.Trial = None) -> Dict[str, Any]:
        if trial is None:
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
            }
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
        }

    def create_controller(
        self,
        env: Env,
        config_path: str = None,
        environment_provider: IEnvironmentProvider = None,
        environment_config: str = None,
    ) -> IRLController:
        raise NotImplementedError("create_controller not required for this test")


# ---- Fixtures ----


@pytest.fixture
def controller_provider():
    return DummyRLControllerProvider()


# ---- TESTS ----


def test_suggest_hyperparameters_merges_fixed(controller_provider):
    trial = optuna.trial.FixedTrial({"learning_rate": 0.0002, "gamma": 0.95})
    fixed = {"gamma": 0.5}
    result = controller_provider._suggest_hyperparameters(trial, fixed)
    assert result["learning_rate"] == 0.0002
    assert result["gamma"] == 0.5


def test_tune_hyperparameters_combines_trial_and_fixed(controller_provider):
    env_mock = Mock()
    ctrl_mock = DummyController(env_mock)
    ctrl_mock.train = Mock()
    ctrl_mock.get_action = Mock(return_value=0)

    controller_provider._build_controller = Mock(return_value=ctrl_mock)

    env_provider = Mock()
    env_provider.create_environment.return_value = env_mock

    # Patch Experiment to return fixed reward
    from experiment.experiment import Experiment

    Experiment.run = lambda self: [42.0]

    result = controller_provider._tune_hyperparameters(
        env_provider=env_provider,
        env_config="mock_config",
        num_trials=1,
        num_episodes=1,
        fixed_hyperparams={"gamma": 0.8},
    )

    assert isinstance(result, dict)
    assert result["gamma"] == 0.8
    assert "learning_rate" in result


def test_create_rl_controller_executes_training(controller_provider):
    env = Mock(spec_set=gymnasium.Env)
    env_provider = Mock()
    env_provider.create_environment.return_value = env

    controller = controller_provider.create_rl_controller(
        env=env,
        environment_provider=env_provider,
        environment_config="any",
        train_timesteps=10,
        is_continuous_action_space=True,
        num_trials=1,
        num_episodes=1,
        hyperparameters={"learning_rate": 1e-4, "gamma": 0.9},
    )

    assert isinstance(controller, IRLController)
    assert controller.env.unwrapped is env.unwrapped
    assert controller.trained_timesteps == 10
