from typing import Any

import gymnasium
from stable_baselines3 import SAC

from controllers.base_controller import IController
from controllers.controller_provider import IControllerProvider
from custom_loggers.experiment_logger import logger


class SACController(IController):

    def __init__(self, model, env: gymnasium.Env, **kwargs: Any):
        logger.info("Initializing SAC controller")
        super().__init__(env, **kwargs)
        self.model = model

        logger.info("Train SAC controller")
        self.model.learn(total_timesteps=50)

    def get_action(self, state: Any) -> Any:
        action, _ = self.model.predict(state)
        return action


class SACProvider(IControllerProvider):
    def create_controller(self, env: gymnasium.Env, config_path: str | None = None) -> SACController:
        # Communicate to env that SAC support only continuous action space.
        env.continuous_action_space = True

        model = SAC(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,  # Try adjusting this
            ent_coef=0.1,  # Let SAC automatically adjust the entropy coefficient
            target_entropy=0,  # Experiment with this value; lower values reduce exploration
        )

        return SACController(model, env)
