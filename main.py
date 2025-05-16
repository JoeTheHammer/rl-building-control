import typer

from environments.sinergym_provider import SinergymProvider
from simulation.manager import ExperimentManager

app = typer.Typer()


@app.command()
def run(config: str = typer.Argument(..., help="Path to the YAML config file")):

    experiment_manager = ExperimentManager()
    experiment_manager.register_environment_provider("sinergym", SinergymProvider())

if __name__ == "__main__":
    app()
