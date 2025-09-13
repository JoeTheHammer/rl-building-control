import unittest

import numpy as np
from gymnasium.spaces import Box, Discrete

from spaces.custom_action_space import ActuatorActionSpace


class TestActuatorActionSpace(unittest.TestCase):

    def test_discrete_action_to_eplus(self):
        # Should map discrete index to real actuator value
        action_space = ActuatorActionSpace([Discrete(3)], [[10.0, 20.0, 30.0]])
        result = action_space.to_eplus_action(np.array([2]))
        np.testing.assert_array_equal(result, np.array([30.0], dtype=np.float32))

    def test_box_action_to_eplus(self):
        # Should pass through Box action as float
        action_space = ActuatorActionSpace(
            [Box(low=np.array([0.0]), high=np.array([1.0]), dtype=np.float32)], [None]
        )
        result = action_space.to_eplus_action(np.array([[0.7]]))
        np.testing.assert_array_equal(result, np.array([0.7], dtype=np.float32))

    def test_mixed_action_to_eplus(self):
        # Should map discrete and pass through continuous for a mixed space
        spaces = [Discrete(2), Box(low=np.array([0.0]), high=np.array([1.0]), dtype=np.float32)]
        mappings = [[100.0, 200.0], None]
        action_space = ActuatorActionSpace(spaces, mappings)
        action = np.array([0, np.array([0.5])], dtype=object)
        result = action_space.to_eplus_action(action)
        np.testing.assert_array_equal(result, np.array([100.0, 0.5], dtype=np.float32))

    def test_multidim_box_action_to_eplus(self):
        # Should flatten multidimensional box
        space = Box(low=np.array([0.0, 1.0]), high=np.array([1.0, 2.0]), dtype=np.float32)
        action_space = ActuatorActionSpace([space], [None])
        result = action_space.to_eplus_action(np.array([[0.2, 1.8]]))
        np.testing.assert_array_equal(
            result, np.array([0.2], dtype=np.float32)
        )  # Only first dimension used

    def test_get_box_space_discrete(self):
        # Should reflect min/max of mapping in box space for discrete actuator
        mapping = [2.5, 7.2, 10.3]
        action_space = ActuatorActionSpace([Discrete(3)], [mapping])
        box = action_space.get_box_space()
        np.testing.assert_array_equal(box.low, np.array([2.5], dtype=np.float32))
        np.testing.assert_array_equal(box.high, np.array([10.3], dtype=np.float32))

    def test_get_box_space_box(self):
        # Should reflect original Box bounds
        box_space = Box(low=np.array([2.0]), high=np.array([5.0]), dtype=np.float32)
        action_space = ActuatorActionSpace([box_space], [None])
        box = action_space.get_box_space()
        np.testing.assert_array_equal(box.low, np.array([2.0], dtype=np.float32))
        np.testing.assert_array_equal(box.high, np.array([5.0], dtype=np.float32))

    def test_get_box_space_mixed(self):
        # Should flatten to one Box and reflect correct bounds for all actuators
        spaces = [
            Discrete(2),
            Box(low=np.array([1.0]), high=np.array([2.0]), dtype=np.float32),
            Box(low=np.array([0.0, 5.0]), high=np.array([1.0, 10.0]), dtype=np.float32),
        ]
        mappings = [[10.0, 30.0], None, None]
        action_space = ActuatorActionSpace(spaces, mappings)
        box = action_space.get_box_space()
        np.testing.assert_array_equal(box.low, np.array([10.0, 1.0, 0.0, 5.0], dtype=np.float32))
        np.testing.assert_array_equal(box.high, np.array([30.0, 2.0, 1.0, 10.0], dtype=np.float32))

    def test_missing_discrete_mapping_raises(self):
        # Should raise if Discrete mapping is missing or empty
        with self.assertRaises(ValueError):
            ActuatorActionSpace([Discrete(2)], [None]).get_box_space()
        with self.assertRaises(ValueError):
            ActuatorActionSpace([Discrete(2)], [[]]).get_box_space()

    # ---- New: map_continuous_to_valid_actions ----

    def test_map_continuous_to_valid_actions_discrete(self):
        # Should map to nearest discrete value
        action_space = ActuatorActionSpace([Discrete(3)], [[-1.0, 5.0, 9.0]])
        # Closest to 6.9 is 5.0, closest to 7.8 is 9.0, closest to -2 is -1.0
        actions = [6.9, 7.8, -2]
        expected = [5.0, 9.0, -1.0]
        for act, exp in zip(actions, expected):
            result = action_space.map_continuous_to_valid_actions(np.array([act]))
            np.testing.assert_array_equal(result, np.array([exp], dtype=np.float32))

    def test_map_continuous_to_valid_actions_box(self):
        # Should pass through Box value as is
        action_space = ActuatorActionSpace(
            [Box(low=np.array([0.0]), high=np.array([2.0]), dtype=np.float32)], [None]
        )
        result = action_space.map_continuous_to_valid_actions(np.array([[1.7]]))
        np.testing.assert_array_equal(result, np.array([1.7], dtype=np.float32))

    def test_map_continuous_to_valid_actions_mixed(self):
        # Should correctly map discrete and pass through box in mixed space
        spaces = [Discrete(2), Box(low=np.array([0.0]), high=np.array([1.0]), dtype=np.float32)]
        mappings = [[10.0, 20.0], None]
        action_space = ActuatorActionSpace(spaces, mappings)
        action = np.array([12.2, np.array([0.8])], dtype=object)  # Closest discrete is 10.0
        result = action_space.map_continuous_to_valid_actions(action)
        np.testing.assert_array_equal(result, np.array([10.0, 0.8], dtype=np.float32))

    def test_map_continuous_to_valid_actions_with_array_input(self):
        # Should handle array-like input for discrete
        action_space = ActuatorActionSpace([Discrete(3)], [[2.0, 4.0, 8.0]])
        # Controller outputs a 0-dim numpy array (can happen in some RL libs)
        val = np.array(7.9)
        result = action_space.map_continuous_to_valid_actions(np.array([val]))
        np.testing.assert_array_equal(result, np.array([8.0], dtype=np.float32))
