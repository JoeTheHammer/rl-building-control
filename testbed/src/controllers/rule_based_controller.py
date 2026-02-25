from typing import Any, Dict, List, Optional

import gymnasium as gym
import numpy as np
import yaml
from asteval import Interpreter
from pydantic import BaseModel

from controllers.base_controller import ControllerSetup, Controller, ControllerFactory
from environments.sinergym_factory import SinergymFactory
from parser.config_parser import parse_sinergym_environment_config
from reward.expression_reward import within
from utils.seeding import seed_env_spaces
from wrappers.continuous_action_wrapper import ContinuousActionWrapper


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


def load_rule_based_controller_config(path: str) -> RuleBasedControllerConfig:
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


class RuleBasedController(Controller):
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
        # Ensure continuous actions are used for Sinergym
        env = ContinuousActionWrapper(env)
        super().__init__(env)

        self.rules = rules
        self.state_space = state_space
        self.custom_variables = custom_variables
        self.aeval = Interpreter(
            usersyms={
                "abs": abs,
                "min": min,
                "max": max,
                "exp": np.exp,
                "clip": np.clip,
                "sqrt": np.sqrt,
                "within": within,
            },
            no_print=True,
        )
        # Add after init — ensures it’s not removed from safe symbols
        self.aeval.symtable["list"] = list

    def _extract_state_values(self, state: Any) -> Dict[str, float]:
        """
        Build a named state dictionary from either a NumPy array or a dict observation.
        - If ndarray: assumes order in state_space == order in observation vector.
        - If dict: matches by key, with fuzzy fallback for underscores/spaces.
        """

        # Case 1: Numeric array (Sinergym’s usual format)
        if isinstance(state, np.ndarray):
            return {name: float(state[i]) for i, name in enumerate(self.state_space)}

        # Case 2: Dictionary observation (some wrappers may use this)
        elif isinstance(state, dict):
            state_dict: Dict[str, float] = {}
            for var in self.state_space:
                # Try exact key match
                if var in state:
                    state_dict[var] = float(state[var])
                    continue

                # Try fuzzy match: ignore case, underscores, spaces
                normalized_var = var.replace("_", "").lower()
                match = None
                for key in state.keys():
                    if key.replace(" ", "").replace("_", "").lower() == normalized_var:
                        match = key
                        break

                if match:
                    state_dict[var] = float(state[match])
                else:
                    raise KeyError(
                        f"Variable '{var}' not found in observation keys: {list(state.keys())}"
                    )

            return state_dict

        else:
            raise TypeError(f"Unsupported observation type: {type(state)}")

    def get_action(self, state: Any) -> Any:
        """
        Returns an action based on the first matching rule condition that is found.

        Args:
            state (Any): The current environment observation (np.ndarray or dict).

        Returns:
            Any: The action as returned by the evaluated rule expression.

        Raises:
            ValueError: If a rule condition or action fails to evaluate.
            RuntimeError: If no rule condition matches the current state.
        """

        # Create name→value mapping
        state_dict = self._extract_state_values(state)

        # Prepare evaluator context
        self.aeval.symtable.clear()

        self.aeval = Interpreter(
            usersyms={
                "abs": abs,
                "min": min,
                "max": max,
                "exp": np.exp,
                "clip": np.clip,
                "sqrt": np.sqrt,
                "within": within,
            },
            no_print=True,
        )
        # Add after init — ensures it’s not removed from safe symbols
        self.aeval.symtable["list"] = list

        self.aeval.symtable.update(self.custom_variables)
        self.aeval.symtable.update(state_dict)

        # Evaluate rules in order
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
                expr = rule.action.strip()

                # Evaluate directly — asteval now supports list literals and expressions
                action_result = self.aeval(expr)

                if self.aeval.error:
                    raise ValueError(
                        f"Error in action '{rule.action}':\n"
                        + "\n".join(err.get_error() for err in self.aeval.error)
                    )

                # Ensure numeric numpy array output
                return np.array(action_result, dtype=np.float32)
        return None


class RuleBasedControllerFactory(ControllerFactory):
    def create_controller_setup(self) -> ControllerSetup:
        if not self.config_path:
            raise ValueError("A config_path is required for RuleBasedController.")

        controller_config = load_rule_based_controller_config(self.config_path)

        env = self.env_factory.create_environment()
        seed_env_spaces(env, self.seed)

        # For sinergym environment, state space can be read out of config.
        if isinstance(self.env_factory, SinergymFactory):
            env_config = parse_sinergym_environment_config(self.env_factory.config_path)
            state_space = list(env_config.state_space.variables.keys()) + list(
                env_config.state_space.meters.keys()
            )
        else:
            # For other (future) environments: state space can be passed.
            state_space = controller_config.state_space

        controller = RuleBasedController(
            env=env,
            rules=controller_config.rules,
            state_space=state_space,
            custom_variables=controller_config.custom_variables or {},
        )

        return ControllerSetup(controller, env)
