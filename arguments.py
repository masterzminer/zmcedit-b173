import argparse
from pathlib import Path


def validate_dir(dir: str):
    path = Path(dir)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {dir}")
    return path


# Parse arguments
def init():
    """
    Initialize all values for all arguments
    """

    parser = argparse.ArgumentParser(
        description=f"A port of MC Edit for Minecraft Beta 1.7.3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--config",
        type=validate_dir,
        help="Path to custom configuration directory"
    )

    parser.add_argument(
        "--installed",
        type=validate_dir,
        help="Path to custom install directory"
    )

    return parser.parse_args();

parsed_args = init()


# Values from command line arguments
CONFIG_OVERRIDE = parsed_args.config
"""Path override for config directory"""
INSTALLED_OVERRIDE = parsed_args.installed
"""Path override for install directory"""
