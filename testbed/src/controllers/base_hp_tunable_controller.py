from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import optuna

from controllers.base_rl_controller import IRLControllerFactory


class IHPTunableControllerFactory(IRLControllerFactory, ABC):
    @abstractmethod
    def suggest_hyperparameters_space(self, trial: Optional[optuna.Trial] = None) -> Dict[str, Any]:
        """
        Suggest a set of hyperparameters available for this controller.

        Args:
           trial (optuna.Trial | None): The current Optuna trial. If None, defaults are used.

        Returns:
           Dict: Dictionary containing suggested or fixed hyperparameters.
        """
        pass
