import sys

# Values from command line arguments

CONFIG_OVERRIDE = None
"""Path override for config directory"""

INSTALLED_OVERRIDE = None
"""Path override for install directory"""

# Parse arguments
args = sys.argv
for (i, arg) in enumerate(args):
    if arg == "--config":
        if len(args) < i + 1:
            raise Exception("--config requires a directory")
        CONFIG_OVERRIDE = args[i + 1]

    if arg == "--installed":
        if len(args) < i + 1:
            raise Exception("--installed requires a directory")
        INSTALLED_OVERRIDE = args[i + 1]