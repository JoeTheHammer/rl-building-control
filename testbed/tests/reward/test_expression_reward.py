import numpy as np

from reward.expression_reward import ExpressionReward


def test_exact_target_temperature_reward():
    reward_fn = ExpressionReward(
        expression="2 * exp(-((air_temp_101 - target_temp)**2) / (2 * sigma**2)) - 1",
        params={"target_temp": 23.0, "sigma": 1.0},
    )
    reward, info = reward_fn({"air_temp_101": 23.0, "__compute_reward__": True})
    assert abs(reward - 1.0) < 1e-6
    assert info["reward"] == reward


def test_temperature_above_target():
    reward_fn = ExpressionReward(
        expression="2 * exp(-((air_temp_101 - target_temp)**2) / (2 * sigma**2)) - 1",
        params={"target_temp": 23.0, "sigma": 1.0},
    )
    reward, _ = reward_fn({"air_temp_101": 24.0, "__compute_reward__": True})
    expected = 2 * np.exp(-((24.0 - 23.0) ** 2) / (2 * 1.0**2)) - 1
    assert abs(reward - expected) < 1e-6


def test_temperature_below_target():
    reward_fn = ExpressionReward(
        expression="2 * exp(-((air_temp_101 - target_temp)**2) / (2 * sigma**2)) - 1",
        params={"target_temp": 23.0, "sigma": 1.0},
    )
    reward, _ = reward_fn({"air_temp_101": 22.0, "__compute_reward__": True})
    expected = 2 * np.exp(-((22.0 - 23.0) ** 2) / (2 * 1.0**2)) - 1
    assert abs(reward - expected) < 1e-6


def test_action_penalty_in_expression():
    reward_fn = ExpressionReward(
        expression="1.0 - abs(action - target_temp) * 0.1", params={"target_temp": 23.0}
    )
    reward, _ = reward_fn({"action": 25.0, "__compute_reward__": True})
    expected = 1.0 - abs(25.0 - 23.0) * 0.1
    assert abs(reward - expected) < 1e-6


def test_combined_temp_and_action_expression():
    reward_fn = ExpressionReward(
        expression="(2 * exp(-((air_temp_101 - target_temp)**2) / (2 * sigma**2)) - 1) - abs(action - target_temp) * 0.1",
        params={
            "target_temp": 23.0,
            "sigma": 1.0,
        },
    )
    reward, _ = reward_fn({"air_temp_101": 23.0, "action": 25.0, "__compute_reward__": True})
    expected = (2 * np.exp(-((23.0 - 23.0) ** 2) / (2 * 1.0**2)) - 1) - abs(25.0 - 23.0) * 0.1
    assert abs(reward - expected) < 1e-6


def test_use_one_part_of_dict():
    reward_fn = ExpressionReward(expression="2 * day_sin", params={})
    reward, _ = reward_fn({"day_sin": 20.0, "__compute_reward__": True})
    expected = 2 * 20.0

    assert abs(reward - expected) < 1e-6
