import unittest

import numpy as np
from gymnasium.spaces import Box, Discrete

from spaces.custom_action_space import ActuatorActionSpace


class TestActuatorActionSpace(unittest.TestCase):

    def test_discrete_action_conversion(self):
        # Tests if a discrete action is correctly mapped to its corresponding real value.
        space = Discrete(3)
        mapping = [10.0, 20.0, 30.0]
        action_space = ActuatorActionSpace([space], [mapping])

        action = np.array([1])  # should map to 20.0
        result = action_space.to_eplus_action(action)
        np.testing.assert_array_equal(result, np.array([20.0], dtype=np.float32))

    def test_box_action_conversion(self):
        # Tests if a single-dimensional Box action is correctly passed through as float.
        space = Box(low=np.array([0.0]), high=np.array([1.0]), dtype=np.float32)
        action_space = ActuatorActionSpace([space], [None])

        action = np.array([[0.75]])
        result = action_space.to_eplus_action(action)
        np.testing.assert_array_equal(result, np.array([0.75], dtype=np.float32))

    def test_mixed_action_conversion(self):
        # Tests if a combination of Discrete and Box actions is correctly mapped and flattened.
        spaces = [Discrete(2), Box(low=np.array([0.0]), high=np.array([1.0]), dtype=np.float32)]
        mappings = [[100.0, 200.0], None]
        action_space = ActuatorActionSpace(spaces, mappings)

        action = np.array([1, np.array([0.5])], dtype=object)
        result = action_space.to_eplus_action(action)
        np.testing.assert_array_equal(result, np.array([200.0, 0.5], dtype=np.float32))

    def test_multidim_box_handling(self):
        # Tests if a 2D Box space is flattened correctly to produce the full value bounds.
        space = Box(low=np.array([0.0, 1.0]), high=np.array([1.0, 2.0]), dtype=np.float32)
        action_space = ActuatorActionSpace([space], [None])

        box = action_space.get_box_space()
        self.assertEqual(box.shape, (2,))
        np.testing.assert_array_equal(box.low, np.array([0.0, 1.0], dtype=np.float32))
        np.testing.assert_array_equal(box.high, np.array([1.0, 2.0], dtype=np.float32))

    def test_get_box_space_with_mixed_spaces(self):
        # Tests if a combination of Discrete and multi-dimensional Box spaces is flattened into one Box.
        spaces = [
            Discrete(3),
            Box(low=np.array([1.0]), high=np.array([2.0]), dtype=np.float32),
            Box(low=np.array([0.0, 5.0]), high=np.array([1.0, 10.0]), dtype=np.float32),
        ]
        mappings = [[10.0, 20.0, 30.0], None, None]
        action_space = ActuatorActionSpace(spaces, mappings)

        box = action_space.get_box_space()
        np.testing.assert_array_equal(box.low, np.array([10.0, 1.0, 0.0, 5.0], dtype=np.float32))
        np.testing.assert_array_equal(box.high, np.array([30.0, 2.0, 1.0, 10.0], dtype=np.float32))

    def test_missing_mapping_raises(self):
        # Tests if an error is raised when a Discrete space has no mapping provided.
        with self.assertRaises(ValueError):
            ActuatorActionSpace([Discrete(2)], [None]).get_box_space()
