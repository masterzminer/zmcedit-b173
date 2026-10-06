import sys

# Values from command line arguments

# Path override for config directory
CONFIG_OVERRIDE = None


# Parse arguments
args = sys.argv
for (i, arg) in enumerate(args):
    if arg == "--config":
        if len(args) < i + 1:
            raise Exception("--config requires a directory")
        CONFIG_OVERRIDE = args[i + 1]