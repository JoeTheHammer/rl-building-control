import sys
import os
import unittest
from unittest.mock import patch, mock_open
import yaml

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.yaml_controller import save_controller
from models.controller import SaveControllerRequest, ControllerSettings, KV, EnvironmentWrapper

class TestYamlController(unittest.TestCase):
    def test_save_controller_with_nested_hyperparameters(self):
        # Arrange
        req = SaveControllerRequest(
            filename="test_controller.yaml",
            directory="config/controllers",
            settings=ControllerSettings(
                type="reinforcement learning",
                hyperparameters=[
                    KV(key="policy_kwargs.squash_output", value="True"),
                    KV(key="learning_rate", value="0.0003"),
                    KV(key="n_steps", value="2048"),
                ],
                trainingTimesteps=1000,
                reportTraining=False,
                denormalize=False,
                tensorboardLogs=False,
                hpTuning=False,
                environmentWrapper=EnvironmentWrapper(),
            ),
        )

        # Act
        m = mock_open()
        with patch("pathlib.Path.open", m):
            with patch("pathlib.Path.mkdir"):
                 save_controller(req)

        # Assert
        handle = m()
        written_content = "".join(c[0][0] for c in handle.write.call_args_list)

        # Parse the YAML content to verify its structure and types
        parsed_yaml = yaml.safe_load(written_content)

        hyperparameters = parsed_yaml.get("hyperparameters", {})
        self.assertIn("policy_kwargs", hyperparameters)
        self.assertIn("squash_output", hyperparameters["policy_kwargs"])
        self.assertEqual(hyperparameters["policy_kwargs"]["squash_output"], True)
        self.assertIsInstance(hyperparameters["policy_kwargs"]["squash_output"], bool)

        self.assertIn("learning_rate", hyperparameters)
        self.assertEqual(hyperparameters["learning_rate"], 0.0003)
        self.assertIsInstance(hyperparameters["learning_rate"], float)

        self.assertIn("n_steps", hyperparameters)
        self.assertEqual(hyperparameters["n_steps"], 2048)
        self.assertIsInstance(hyperparameters["n_steps"], int)

    def test_conflicting_keys(self):
        from services.yaml_controller import _build_nested_dict

        with self.assertRaisesRegex(ValueError, "Key conflict: 'a' is a leaf node and cannot have sub-keys."):
            _build_nested_dict([KV(key="a", value="1"), KV(key="a.b", value="2")])

        with self.assertRaisesRegex(ValueError, "Key conflict: 'a.b' is a parent node and cannot be assigned a value."):
            _build_nested_dict([KV(key="a.b.c", value="1"), KV(key="a.b", value="2")])


if __name__ == "__main__":
    unittest.main()
