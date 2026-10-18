import argparse
from pathlib import Path


def validate_dir(dir: str):
    path = Path(dir)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {dir}")
    return path


def validate_dat_file(file: str):
    path = Path(file)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Value is not a file or does not exist: {file}")
    
    if path.stem != "level" or path.suffix != ".dat":
        raise argparse.ArgumentTypeError(f"File is not a level.dat file: {file}")
        
    return path


# Parse arguments
def init():
    """
    Initialize all values for all arguments
    """

    parser = argparse.ArgumentParser(
        description="A port of MC Edit for Minecraft Beta 1.7.3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--config",
        type=validate_dir,
        help="Path to custom configuration directory, stores config file, logs, etc"
    )

    parser.add_argument(
        "--installed",
        type=validate_dir,
        help="Path to custom install directory, used to access assets directory, readme, etc"
    )

    parser.add_argument(
        "--filters",
        type=validate_dir,
        help="Additional path to custom filters",
        action="append"
    )

    parser.add_argument(
        "--world",
        type=validate_dat_file,
        help="A world to load immediately on start up",
    )

    return parser.parse_args();

parsed_args = init()


# Values from command line arguments
CONFIG_OVERRIDE = parsed_args.config
"""Path override for config directory"""
INSTALLED_OVERRIDE = parsed_args.installed
"""Path override for install directory"""
FILTER_DIRS = parsed_args.filters or []
"""Additional paths for custom filters"""
LOAD_WORLD = parsed_args.world