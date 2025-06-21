from typing import Any, Dict

import optuna
import pytest


# Dummy SACProvider for testing
class DummySACProvider:
    def _suggest_hyperparameters_space(self, trial: optuna.Trial = None) -> Dict[str, Any]:
        if trial is None:
            return {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "ent_coef": "auto_1.0",
                "batch_size": 64,
            }
        return {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-3),
            "gamma": trial.suggest_float("gamma", 0.9, 0.9999),
            "ent_coef": trial.suggest_float("ent_coef", 1e-8, 1e-1),
            "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
        }

    def _suggest_hyperparameters(
        self,
        trial: optuna.Trial = None,
        fixed_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        fixed_params = fixed_params or {}
        suggested = self._suggest_hyperparameters_space(trial)
        return {**suggested, **fixed_params}


@pytest.fixture
def sac_provider():
    return DummySACProvider()


def test_suggest_hyperparameter_space_without_trial(sac_provider):
    result = sac_provider._suggest_hyperparameters_space()
    assert result == {
        "learning_rate": 1e-4,
        "gamma": 0.99,
        "ent_coef": "auto_1.0",
        "batch_size": 64,
    }


def test_suggest_hyperparameter_space_with_trial(sac_provider):
    trial = optuna.trial.FixedTrial({
        "learning_rate": 0.0005,
        "gamma": 0.95,
        "ent_coef": 0.01,
        "batch_size": 128
    })

    result = sac_provider._suggest_hyperparameters_space(trial)
    assert result["learning_rate"] == 0.0005
    assert result["gamma"] == 0.95
    assert result["ent_coef"] == 0.01
    assert result["batch_size"] == 128


def test_suggest_hyperparameters_merge_with_fixed_params(sac_provider):
    trial = optuna.trial.FixedTrial({
        "learning_rate": 0.0001,
        "gamma": 0.92,
        "ent_coef": 0.02,
        "batch_size": 64,
    })

    fixed = {"gamma": 0.5, "batch_size": 32}
    result = sac_provider._suggest_hyperparameters(trial, fixed)
    assert result["learning_rate"] == 0.0001
    assert result["gamma"] == 0.5  # Overridden
    assert result["batch_size"] == 32  # Overridden
    assert result["ent_coef"] == 0.02


def test_suggest_hyperparameters_no_trial_with_fixed(sac_provider):
    fixed = {"ent_coef": "auto_5.0"}
    result = sac_provider._suggest_hyperparameters(None, fixed)
    assert result["learning_rate"] == 1e-4
    assert result["gamma"] == 0.99
    assert result["ent_coef"] == "auto_5.0"
    assert result["batch_size"] == 64
