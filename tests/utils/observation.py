import numpy as np
import pytest

from utils.observation import build_reward_dict


def test_build_observation_dict_multiple_actions():
    variables = {
        "air_temp_101": ("Zone Mean Air Temperature", "GUESTROOM101"),
        "humidity_101": ("Zone Mean Air Humidity Ratio", "GUESTROOM101"),
    }
    meters = {
        "electricity": "Electricity:Facility",
        "gas": "NaturalGas:Facility",
    }
    actuators = {
        "temp_setpoint": ("Zone Temperature Control", "Temperature", "GUESTROOM101"),
        "gas_setpoint": ("Zone Gas Control", "Gas", "GAS"),
    }

    obs = np.array([22.0, 0.002, 48000000.0, 47000000.0], dtype=np.float32)
    action = np.array([23.0, 555], dtype=np.float32)
    info = {"timestep": 42, "episode": 1}

    result = build_reward_dict(obs, action, info, variables, meters, actuators)

    expected = {
        "air_temp_101": pytest.approx(22.0),
        "humidity_101": pytest.approx(0.002),
        "electricity": pytest.approx(48000000.0),
        "gas": pytest.approx(47000000.0),
        "temp_setpoint": pytest.approx(23.0),
        "gas_setpoint": pytest.approx(555),
        "timestep": 42,
        "episode": 1,
    }

    assert result == expected

def test_build_observation_dict_one_action():
    variables = {
        "air_temp_101": ("Zone Mean Air Temperature", "GUESTROOM101"),
        "humidity_101": ("Zone Mean Air Humidity Ratio", "GUESTROOM101"),
    }
    meters = {
        "electricity": "Electricity:Facility",
        "gas": "NaturalGas:Facility",
    }
    actuators = {
        "temp_setpoint": ("Zone Temperature Control", "Temperature", "GUESTROOM101"),
    }

    obs = np.array([22.0, 0.002, 48000000.0, 47000000.0], dtype=np.float32)
    action = np.array([23.0], dtype=np.float32)
    info = {"timestep": 42, "episode": 1}

    result = build_reward_dict(obs, action, info, variables, meters, actuators)

    expected = {
        "air_temp_101": pytest.approx(22.0),
        "humidity_101": pytest.approx(0.002),
        "electricity": pytest.approx(48000000.0),
        "gas": pytest.approx(47000000.0),
        "temp_setpoint": pytest.approx(23.0),
        "timestep": 42,
        "episode": 1,
    }

    assert result == expected