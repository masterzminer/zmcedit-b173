"""Copyright (c) 2026 masterzminer

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""


import os
from pathlib import Path
import sys
import arguments

# If there is no "frozen" attribute set to true, then this is running directly as python, i.e. running from source
FROZEN = getattr(sys, "frozen", False)

# Names of directories
ASSETS_NAME = "assets"
CONFIG_NAME = ".zmcedit-b173"
STOCK_SCHEMATICS_NAME = "stock-schematics"
STOCK_FILTERS_NAME = "filters"
LOG_NAME = "mcedit.log"
INI_NAME = "mcedit.ini"
DEMO_DIR_NAME = "demo"
ITEMS_NAME = "items.txt"
TEMPLATE_NAME = "template.py"
GUIDE_NAME = "guide.py"

_CONFIG_OVERRIDEN = arguments.INSTALLED_OVERRIDE is not None
_INSTALL_OVERRIDEN = arguments.CONFIG_OVERRIDE is not None

def findDirectories():
    
    # If a command line path is not provided for where to read install data from, use the defaults
    if arguments.INSTALLED_OVERRIDE is None:
        if FROZEN:
            # This is running from pyinstaller, go from the temp directory
            install_root = Path(sys._MEIPASS)
        else:
            # This is running from source, use the root of the project
            install_root = Path(__file__).resolve().parent
    
    # Otherwise, use the given dir
    else:
        install_root = arguments.INSTALLED_OVERRIDE


    # If a command line config path is not provided, use defaults
    if arguments.CONFIG_OVERRIDE is None:
        # This is running from pyinstaller, go from the root path
        if FROZEN: config_root = Path.home()
        # This is running from source, use the root of the project
        else: config_root = Path(__file__).resolve().parent

        config = config_root / CONFIG_NAME

    # Otherwise, use the given config
    else:
        config = arguments.CONFIG_OVERRIDE

    # Now that the config is loaded, log information from start up

    os.makedirs(config, exist_ok=True)

    assets = install_root / ASSETS_NAME

    stock_schematics = assets / STOCK_SCHEMATICS_NAME

    stock_filters = install_root / STOCK_FILTERS_NAME
    os.makedirs(stock_filters, exist_ok=True)

    return install_root, config, assets, stock_schematics, stock_filters


# Absolute paths to files and directories
INSTALL_ROOT, CONFIG, ASSETS, STOCK_SCHEMATICS, STOCK_FILTERS = findDirectories()

LOG_FILE = CONFIG / LOG_NAME
INI_FILE = CONFIG / INI_NAME
ITEMS_FILE = ASSETS / ITEMS_NAME
FILTER_TEMPLATE_FILE = STOCK_FILTERS / DEMO_DIR_NAME / TEMPLATE_NAME
FILTER_GUIDE_FILE = STOCK_FILTERS / DEMO_DIR_NAME / GUIDE_NAME

# Must log all details about directories after setting up files due to circular logic
def _log_creation():
    import log
    if FROZEN:
        log.info("Running from stand alone install")
    else:
        log.info("Running from source")

    global _CONFIG_OVERRIDEN, _INSTALL_OVERRIDEN

    if _CONFIG_OVERRIDEN:
        log.info("Config directory overriden to:", arguments.CONFIG_OVERRIDE)

    if _INSTALL_OVERRIDEN:
        log.info("Install directory overriden to:", arguments.INSTALLED_OVERRIDE)

    log.info("Loaded install data from dir:", INSTALL_ROOT)
    log.info("Loaded config data from dir:", CONFIG)

_log_creation()