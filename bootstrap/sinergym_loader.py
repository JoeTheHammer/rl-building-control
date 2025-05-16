import site
import sys
from pathlib import Path

from custom_loggers.setup_logger import logger

ENERGY_PLUS_PATH_FILENAME = "energyplus_path.pth"


def check_energyplus_path() -> bool:
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


def create_sinergym_provider():
    if not check_energyplus_path():
        sys.exit(1)

    try:
        # Do the import *after* the check
        from environments.sinergym_provider import SinergymProvider

        return SinergymProvider()
    except ImportError as e:
        logger.error("Could not import SinergymProvider or dependencies.")
        logger.error("Make sure the EnergyPlus path is correctly set and contains 'pyenergyplus'.")
        logger.debug(f"Original error: {e}")
        sys.exit(1)
