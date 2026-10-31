import argparse
from pathlib import Path


def _validate_dir(dir: str):
    path = Path(dir)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {dir}")
    return path


def _validate_dat_file(file: str):
    path = Path(file)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Value is not a file or does not exist: {file}")
    
    if path.stem != "level" or path.suffix != ".dat":
        raise argparse.ArgumentTypeError(f"File is not a level.dat file: {file}")
        
    return path

def _validate_position(pos_str: str):
    try:
        return tuple(map(float, pos_str.split(',')))
    except:
        raise argparse.ArgumentTypeError(f"Position '{pos_str}' invalid must be 3 comma separated numbers as x,y,z")


def _validate_look(look_str: str):
    try:
        return tuple(map(float, look_str.split(',')))
    except:
        raise argparse.ArgumentTypeError(f"Direction '{look_str}' invalid must be 2 comma separated numbers as yaw,pitch")


# Parse arguments
def _init():
    """
    Initialize all values for all arguments
    """

    parser = argparse.ArgumentParser(
        description="A port of MC Edit for Minecraft Beta 1.7.3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="True to enable debug logging"
    )

    parser.add_argument(
        "--debugrender",
        action="store_true",
        help="True to enable additional debug rendering"
    )

    parser.add_argument(
        "--config",
        type=_validate_dir,
        help="Path to custom configuration directory, stores config file, logs, etc"
    )

    parser.add_argument(
        "--installed",
        type=_validate_dir,
        help="Path to custom install directory, used to access assets directory, readme, etc"
    )

    parser.add_argument(
        "--filters",
        type=_validate_dir,
        help="Additional path to custom filters",
        action="append"
    )

    parser.add_argument(
        "--world",
        type=_validate_dat_file,
        help="A world to load immediately on start up",
    )

    parser.add_argument(
        "--pos",
        type=_validate_position,
        help="When loading a world immediately, the position in the world to load into as x,y,z",
    )

    parser.add_argument(
        "--look",
        type=_validate_look,
        help="When loading a world immediately, the direction in degrees for the player to look at as yaw,pitch",
    )

    parser.add_argument(
        "--overworld",
        action="store_true",
        help="When loading a world immediately, force load into the overworld instead of the nether",
    )

    parser.add_argument(
        "--nether",
        action="store_true",
        help="When loading a world immediately, force load into the nether instead of the overworld",
    )

    # Parse arguments
    parsed = parser.parse_args()

    # Custom validation
    if parsed.pos and not parsed.world:
        parser.error("--pos requires a --world")
        
    if parsed.look and not parsed.world:
        parser.error("--look requires a --world")

    if parsed.overworld and not parsed.world:
        parser.error("--overworld requires a --world")
    
    if parsed.nether and not parsed.world:
        parser.error("--nether requires a --world")
    
    if parsed.overworld and parsed.nether:
        parser.error("--overworld and --nether are mutually exclusive")
    
    # Return final parsed values
    return parsed

_parsed_args = _init()


# Values from command line arguments
DEBUG = _parsed_args.debug or False
"""True if debug logging is enabled"""
DEBUG_RENDER = _parsed_args.debugrender or False
"""True if debug logging is enabled"""
CONFIG_OVERRIDE = _parsed_args.config
"""Path override for config directory"""
INSTALLED_OVERRIDE = _parsed_args.installed
"""Path override for install directory"""
FILTER_DIRS = _parsed_args.filters or []
"""Additional paths for custom filters"""
LOAD_WORLD = _parsed_args.world
"""Path to a world to load on startup"""
START_POS = _parsed_args.pos
"""Tuple of (x,y,z) position to load into the world on startup"""
START_LOOK = _parsed_args.look
"""Tuple of (yaw,pitch) direction to load into the world on startup"""
START_NETHER = _parsed_args.nether
"""True to load the nether instead of the overworld when loading into the world on startup"""
START_OVERWORLD = _parsed_args.overworld
"""True to load the overworld instead of the nether when loading into the world on startup"""