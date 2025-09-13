import site
import sys
from pathlib import Path

from custom_loggers.setup_logger import logger
from environments.sinergym_factory import SinergymFactory

ENERGY_PLUS_PATH_FILENAME = "energyplus_path.pth"


def check_energyplus_path() -> bool:
    """
    Check if the EnergyPlus path is correctly configured in the Python environment.

    This function searches the system's `site-packages` directories for a `.pth` file
    (specified by the `ENERGY_PLUS_PATH_FILENAME` constant) that should contain the path
    to the EnergyPlus installation. It logs appropriate messages based on whether the file
    exists or not.

    Returns:
        bool: True if the EnergyPlus path file exists, False otherwise.

    Logs:
        - Error if `site-packages` cannot be found.
        - Warning and instructions if the path file is missing.
        - Info if the path is correctly found.
    """
    try:
        site_packages_dir = next(Path(p) for p in site.getsitepackages() if "site-packages" in p)
    except StopIteration:
        logger.error("Could not locate site-packages directory.")
        return False

    pth_file = site_packages_dir / ENERGY_PLUS_PATH_FILENAME

    if not pth_file.exists():
        logger.warning("EnergyPlus path not set correctly.")
        logger.info(
            f"Please create a file named '{ENERGY_PLUS_PATH_FILENAME}' in site-packages with your EnergyPlus path."
        )
        logger.info(f'Example command:\n  echo "/path/to/EnergyPlus" > "{pth_file}"')
        return False

    logger.info("EnergyPlus path found.")
    return True


def create_sinergym_factory() -> SinergymFactory:
    """
    Create and return a `SinergymFactory` instance, ensuring the EnergyPlus environment is correctly configured.

    This function checks for the presence of the EnergyPlus path before attempting to import and
    instantiate the `SinergymFactory`. If the path is not configured or the import fails,
    the program will terminate with an error message.

    Returns:
        SinergymFactory: An instance of the `SinergymFactory` class.

    Raises:
        SystemExit: If the EnergyPlus path is not configured or the `SinergymFactory` cannot be imported.

    Logs:
        - Error if the EnergyPlus path is invalid or missing.
        - Error if the import fails, including a debug message with the original exception.
    """
    if not check_energyplus_path():
        sys.exit(1)

    try:
        # Do the import *after* the check
        from environments.sinergym_factory import SinergymFactory

        return SinergymFactory()
    except ImportError as e:
        logger.error("Could not import SinergymFactory or dependencies.")
        logger.error("Make sure the EnergyPlus path is correctly set and contains 'pyenergyplus'.")
        logger.debug(f"Original error: {e}")
        sys.exit(1)
