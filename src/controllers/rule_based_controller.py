from typing import Any, Dict, List, Optional

import gymnasium as gym
import numpy as np
import yaml
from asteval import Interpreter
from pydantic import BaseModel

from controllers.base_controller import IController
from controllers.controller_provider import IControllerProvider


class Rule(BaseModel):
    """
    Represents a single rule for the rule-based controller.

    Attributes:
        condition (str): A boolean expression to be evaluated.
        action (str): An expression that defines the resulting action when the condition is true.
    """

    condition: str
    action: str


class RuleBasedControllerConfig(BaseModel):
    """
    Configuration model for the rule-based controller.

    Attributes:
        state_space (List[str]): A list of variable names corresponding to indices in the observation vector.
        rules (List[Rule]): A list of conditional rules for decision making.
        custom_variables (Optional[Dict[str, float]]): Optional static variables available in expressions.
    """

    state_space: List[str]
    rules: List[Rule]
    custom_variables: Optional[Dict[str, float]] = {}  # default to empty dict


def load_controller_config(path: str) -> RuleBasedControllerConfig:
    """
    Loads a YAML controller configuration file and parses it into a RuleBasedControllerConfig object.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        RuleBasedControllerConfig: Parsed configuration object.
    """
    with open(path, "r") as f:
        raw_data = yaml.safe_load(f)
    return RuleBasedControllerConfig(**raw_data)


class RuleBasedController(IController):
    """
    Rule-based controller that selects actions by evaluating user-defined rules using current environment state.

    Args:
        env (gym.Env): The Gym environment.
        rules (List[Rule]): A list of conditional rules.
        state_space (List[str]): List of variable names matching the observation vector.
        custom_variables (Dict[str, float]): Custom static variables for rule evaluation.
    """

    def __init__(
        self,
        env: gym.Env,
        rules: List[Rule],
        state_space: List[str],
        custom_variables: Dict[str, float],
    ):
        super().__init__(env)
        self.rules = rules
        self.state_space = state_space
        self.custom_variables = custom_variables
        self.aeval = Interpreter(no_print=True)

    def get_action(self, state: Any) -> Any:
        """
        Returns an action based on the first matching rule condition.

        Args:
            state (Any): The current environment observation (np.ndarray or dict).

        Returns:
            np.ndarray: The action to apply, matching the environment’s action space.

        Raises:
            ValueError: If an expression fails to evaluate.
            RuntimeError: If no rule condition matches the current state.
            NotImplementedError: If the action space is not 1D Box.
        """

        if isinstance(state, np.ndarray):
            if len(state) != len(self.state_space):
                raise ValueError("Mismatch between state vector and state_space length.")
            state_dict = {name: float(state[i]) for i, name in enumerate(self.state_space)}
        else:
            state_dict = dict(state)

        # Inject both state and custom variables into the evaluator
        self.aeval.symtable.clear()
        self.aeval.symtable.update(self.custom_variables)
        self.aeval.symtable.update(state_dict)

        for rule in self.rules:
            self.aeval.error = []
            condition_result = self.aeval(rule.condition)

            if self.aeval.error:
                raise ValueError(
                    f"Error in condition '{rule.condition}':\n"
                    + "\n".join(err.get_error() for err in self.aeval.error)
                )

            if condition_result:
                self.aeval.error = []
                action_result = self.aeval(rule.action)

                if self.aeval.error:
                    raise ValueError(
                        f"Error in action '{rule.action}':\n"
                        + "\n".join(err.get_error() for err in self.aeval.error)
                    )

                if isinstance(
                    self.env.action_space, gym.spaces.Box
                ) and self.env.action_space.shape == (1,):
                    action_scalar = float(action_result)
                    return np.array(
                        [
                            np.clip(
                                action_scalar,
                                self.env.action_space.low[0],
                                self.env.action_space.high[0],
                            )
                        ],
                        dtype=np.float32,
                    )

                raise NotImplementedError("Only 1D Box action spaces supported.")

        raise RuntimeError("No matching rule found.")


class RuleBasedControllerProvider(IControllerProvider):
    def create_controller(self, env: gym.Env, config_path: str | None = None) -> IController:
        if not config_path:
            raise ValueError("A config_path is required for RuleBasedController.")

        controller_config = load_controller_config(config_path)

        return RuleBasedController(
            env=env,
            rules=controller_config.rules,
            state_space=controller_config.state_space,
            custom_variables=controller_config.custom_variables or {},
        )
