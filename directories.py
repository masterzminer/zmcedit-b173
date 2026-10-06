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
FILTERS_NAME = "filters"
LOG_NAME = "mcedit.log"
INI_NAME = "mcedit.ini"


def findDirectories():
    if FROZEN:
        print("Running from stand alone install")
    else:
        print("Running from source")

    
    # If a command line path is not provided for where to read install data from, use the defaults
    if arguments.INSTALLED_OVERRIDE is None:
        if FROZEN:
            # This is running from pyinstaller, go from the temp directory
            read_root = Path(sys._MEIPASS)
        else:
            # This is running from source, use the root of the project
            read_root = Path(__file__).resolve().parent
    
    # Otherwise, use the given dir
    else:
        print("Install directory overriden to:", arguments.INSTALLED_OVERRIDE)
        read_root = Path(arguments.INSTALLED_OVERRIDE)


    # If a command line config path is not provided, use defaults
    if arguments.CONFIG_OVERRIDE is None:
        # This is running from pyinstaller, go from the root path
        if FROZEN: config_root = Path.home()
        # This is running from source, use the root of the project
        else: config_root = Path(__file__).resolve().parent

        config = config_root / CONFIG_NAME

    # Otherwise, use the given config
    else:
        print("Config directory overriden to:", arguments.CONFIG_OVERRIDE)
        config = Path(arguments.CONFIG_OVERRIDE)


    print("Loading read only data from dir:", read_root)
    print("Loading config data from dir:", config)

    os.makedirs(config, exist_ok=True)

    assets = read_root / ASSETS_NAME

    stock_schematics = assets / STOCK_SCHEMATICS_NAME

    filters = read_root / FILTERS_NAME
    os.makedirs(filters, exist_ok=True)

    return read_root, config, assets, stock_schematics, filters


# Absolute paths to files and directories
READ_ROOT, CONFIG, ASSETS, STOCK_SCHEMATICS, FILTERS = findDirectories()

LOG_FILE = CONFIG / LOG_NAME
INI_FILE = CONFIG / INI_NAME