import typer

from bootstrap.sinergym_loader import create_sinergym_factory
from controllers.a2c_controller import A2CFactory
from controllers.custom_controller import CustomControllerFactory
from controllers.ddpg_controller import DDPGFactory
from controllers.dqn_controller import DQNFactory
from controllers.ppo_controller import PPOFactory
from controllers.random_controller import RandomControllerFactory
from controllers.recurrent_ppo_controller import RecurrentPPOFactory
from controllers.rule_based_controller import RuleBasedControllerFactory
from controllers.sac_controller import SACFactory
from controllers.td3_controller import TD3Factory
from custom_loggers.setup_logger import logger
from experiment.manager import ExperimentManager

app = typer.Typer()


@app.command()
def run(config: str = typer.Argument(..., help="Path to the YAML environment_config file")):
    sinergym_factory = create_sinergym_factory()

    experiment_manager = ExperimentManager()

    experiment_manager.register_environment_factory("sinergym", sinergym_factory)

    experiment_manager.register_controller_factory("random", RandomControllerFactory())
    experiment_manager.register_controller_factory("rule-based", RuleBasedControllerFactory())
    experiment_manager.register_controller_factory("sac", SACFactory())
    experiment_manager.register_controller_factory("custom", CustomControllerFactory())
    experiment_manager.register_controller_factory("ppo", PPOFactory())
    experiment_manager.register_controller_factory("recurrent-ppo", RecurrentPPOFactory())
    experiment_manager.register_controller_factory("a2c", A2CFactory())
    experiment_manager.register_controller_factory("ddpg", DDPGFactory())
    experiment_manager.register_controller_factory("td3", TD3Factory())
    experiment_manager.register_controller_factory("dqn", DQNFactory())

    experiment_manager.run_experiments_from_config(config)
    logger.info("All experiments finished.")


if __name__ == "__main__":
    app()
