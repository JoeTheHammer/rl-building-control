import unittest
import yaml
from pydantic import ValidationError

# This is a bit of a hack to get the test running without having to install the testbed as a package
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from controllers.config import RLControllerConfig

class TestConfigParser(unittest.TestCase):
    def test_parse_nested_hyperparameters(self):
        # Arrange
        yaml_content = """
        training:
          timesteps: 1000
        hyperparameters:
          policy_kwargs:
            squash_output: True
          learning_rate: 0.0003
        """
        config_dict = yaml.safe_load(yaml_content)

        # Act
        try:
            config = RLControllerConfig(**config_dict)
            validation_error = None
        except ValidationError as e:
            config = None
            validation_error = e

        # Assert
        self.assertIsNone(validation_error, "Pydantic validation failed")
        self.assertIsNotNone(config)
        self.assertIn("policy_kwargs", config.hyperparameters)
        self.assertIn("squash_output", config.hyperparameters["policy_kwargs"])
        self.assertEqual(config.hyperparameters["policy_kwargs"]["squash_output"], True)
        self.assertEqual(config.hyperparameters["learning_rate"], 0.0003)

if __name__ == "__main__":
    unittest.main()
