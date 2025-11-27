from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

import optuna

from controllers.base_rl_controller import RLControllerFactory


class HPTunableControllerFactory(RLControllerFactory, ABC):
    """
    Abstract base class for reinforcement learning (RL) controller factories that
    support hyperparameter tuning via Optuna.

    Implementations of this interface define:
      - The hyperparameter search space (both continuous and discrete),
      - The default parameter set used when tuning is disabled,
      - Optionally, a fixed grid-based search space for Optuna's GridSampler.

    This allows controllers to be tuned systematically and consistently
    using the shared `tune_hp()` procedure.
    """

    @abstractmethod
    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        """
        Define or suggest the hyperparameter space for this controller.

        When called with an active Optuna trial, this method should use the
        trial's `suggest_*` methods (e.g., `suggest_float`, `suggest_int`,
        `suggest_categorical`) to sample values within predefined bounds.

        When `trial` is None, implementations should return a set of default
        hyperparameter values representing a stable, non-tuned baseline.

        Args:
            trial (Optional[optuna.Trial]): The current Optuna trial instance.
                If None, return a static default configuration instead.

        Returns:
            Dict[str, Any]: A dictionary mapping hyperparameter names to
            either sampled or default values.
        """
        pass

    def get_grid_search_space(self) -> Dict[str, List[Any]]:
        """
        Optionally define a discrete search space for grid-based hyperparameter tuning.

        This method is required when using Optuna's `GridSampler`. It should
        return a mapping from hyperparameter names to a finite list of
        candidate values. Each combination of parameter values will be
        evaluated exhaustively.

        Example:
            ```python
            return {
                "learning_rate": [1e-5, 1e-4, 1e-3],
                "gamma": [0.95, 0.98, 0.99],
                "ent_coef": [0.0, 0.05, 0.1],
            }
            ```

        Returns:
            Dict[str, List[Any]]: A dictionary mapping each hyperparameter
            name to a list of discrete candidate values.
        """
        pass
