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

# Names of directories
ASSETS_NAME = "assets"
CONFIG_NAME = ".mcedit_config"
STOCK_SCHEMATICS_NAME = "stock-schematics"
USER_SCHEMATICS_NAME = "schematics"
FILTERS_NAME = "filters"
LOG_NAME = "mcedit.log"
INI_NAME = "mcedit.ini"


def findDirectories():
    cwd = os.getcwd()
    root = os.path.abspath(cwd)

    config = os.path.abspath(os.path.join(cwd, CONFIG_NAME))
    os.makedirs(config, exist_ok=True)

    assets = os.path.abspath(os.path.join(cwd, ASSETS_NAME))

    stock_schematics = os.path.abspath(os.path.join(assets, STOCK_SCHEMATICS_NAME))

    user_schematics = os.path.join(config, USER_SCHEMATICS_NAME)
    os.makedirs(user_schematics, exist_ok=True)

    filters = os.path.abspath(os.path.join(root, FILTERS_NAME))

    return root, config, assets, stock_schematics, user_schematics, filters


# Absolute paths to files and directories
ROOT, CONFIG, ASSETS, STOCK_SCHEMATICS, USER_SCHEMATICS, FILTERS = findDirectories()

# TODO allow USER to be configurable, load it from file stored in CONFIG, probably make CONFIG default to a per user configuration
USER = CONFIG

LOG_FILE = os.path.join(USER, LOG_NAME)
INI_FILE = os.path.join(USER, INI_NAME)

def asset(filename):
    return os.path.join(ASSETS, filename)