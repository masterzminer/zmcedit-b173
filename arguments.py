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
        "--old-file-browser",
        action="store_true",
        help="Use the built in pygame gui based file browser instead of os native. Use if there are issues with the native os selector"
    )

    return parser.parse_args();

parsed_args = init()


# Values from command line arguments
CONFIG_OVERRIDE = parsed_args.config
"""Path override for config directory"""
INSTALLED_OVERRIDE = parsed_args.installed
"""Path override for install directory"""
OLD_FILE_BROWSER = parsed_args.old_file_browser
"""true to use the built in gui file browser, false otherwise"""
