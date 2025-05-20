import typer

from bootstrap.sinergym_loader import create_sinergym_provider
from custom_loggers.setup_logger import logger
from simulation.manager import ExperimentManager

app = typer.Typer()


@app.command()
def run(config: str = typer.Argument(..., help="Path to the YAML config file")):
    sinergym_provider = create_sinergym_provider()

    experiment_manager = ExperimentManager()
    experiment_manager.register_environment_provider("sinergym", sinergym_provider)
    experiment_manager.setup_experiments(config)

    logger.info("All experiments finished.")


if __name__ == "__main__":
    app()
