from controllers.base_controller import IController
from custom_loggers.experiment_logger import logger
from environments.base_env import IEnvironment


class Experiment:
    def __init__(self, name: str, env: IEnvironment, controller: IController):
        self.name = name
        self.env = env
        self.controller = controller

    def run(self):
        logger.info(f"Experiment {self.name} started.")

        state, _ = self.env.reset()

        done = False
        total_reward = 0

        while not done:
            action = self.controller.get_action(state)
            state, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            total_reward += reward

        print("\n")
        logger.info(f"Total reward: {total_reward}")

        self.env.close()
        print("Experiment Finished!")
