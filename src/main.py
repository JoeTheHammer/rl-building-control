import typer

from bootstrap.sinergym_loader import create_sinergym_provider
from controllers.random_controller import RandomControllerProvider
from controllers.rule_based_controller import RuleBasedControllerProvider
from controllers.sac_controller import SACProvider
from custom_loggers.setup_logger import logger
from experiment.manager import ExperimentManager

app = typer.Typer()


@app.command()
def run(config: str = typer.Argument(..., help="Path to the YAML environment_config file")):
    sinergym_provider = create_sinergym_provider()

    experiment_manager = ExperimentManager()

    experiment_manager.register_environment_provider("sinergym", sinergym_provider)

    experiment_manager.register_controller_provider("random", RandomControllerProvider())
    experiment_manager.register_controller_provider("rule-based", RuleBasedControllerProvider())
    experiment_manager.register_controller_provider("sac", SACProvider())

    experiment_manager.setup_experiments(config)
    experiment_manager.run_all()
    logger.info("All experiments finished.")


if __name__ == "__main__":
    app()
