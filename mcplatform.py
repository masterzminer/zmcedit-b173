"""Copyright (c) 2010-2012 David Rio Vierra

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

"""
mcplatform.py

Platform-specific functions, folder paths
"""

import directories
import os
from os.path import dirname, exists, join
import sys
import traceback
import platform
import subprocess

import crossfiledialog

enc = sys.getfilesystemencoding()

os.environ["YAML_ROOT"] = join(directories.ROOT, "pymclevel")

from albow import request_new_filename, request_old_filename
from pymclevel import items


AppKit = None

lastSchematicsDir = None
lastSaveDir = None
cmd_name = "Ctrl"
option_name = "Alt"

def askOpenFile(title='Select a Minecraft level...', schematics=False):
    file_types = ["mclevel", "dat", "mine", "mine.gz", "schematic"]

    global lastSchematicsDir, lastSaveDir
    initialDir = lastSaveDir
    if schematics:
        initialDir = lastSchematicsDir or directories.STOCK_SCHEMATICS

    def _ask_open():
        try:
            return crossfiledialog.open_file(
                title=title,
                start_dir=initialDir,
                filter=["*." + f for f in file_types]
            )
        except:
            # TODO make a setting to allow using the os native path or not, to force disable it
            # On an exception, fall back to the built in gui selector
            return request_old_filename(traceback, schematics)

    filename = _ask_open()
    
    if filename:
        if schematics:
            lastSchematicsDir = dirname(filename)
        else:
            lastSaveDir = dirname(filename)

    return filename


def askSaveSchematic(initialDir: str, defaultName: str, filetype: str):
    return askSaveFile(initialDir,
                title='Save this schematic...',
                defaultName=defaultName,
                filetype=filetype
            )


def askCreateWorld(initialDir: str):
    # Find a valid name for a folder that doesn't already exist
    defaultName = name = "Untitled World"
    i = 0
    while exists(join(initialDir, name)):
        i += 1
        name = defaultName + " " + str(i)

    # Select the directory
    return askSaveFile(initialDir, title='Name this new world', defaultName=defaultName)


def askSaveFolder(initialDir, title):
    return crossfiledialog.choose_folder(
        start_dir=initialDir,
        title=title
    )

def askSaveFile(initialDir: str, title: str, defaultName, filetype: str=None):
    # TODO make an option to force using the built in gui file selector
    useOldFile = False;
    if useOldFile:
        return request_new_filename(
            prompt=title,
            suffix=("" if filetype is None else ("." + filetype)),
            directory=initialDir,
            filename=defaultName,
            pathname=None
        )
    else:
        selected_path = crossfiledialog.save_file(
            start_dir=(initialDir if defaultName is None else os.path.join(initialDir, defaultName)),
            title=title,
        )
        if filetype is not None:
            selected_path += "." + filetype
        return selected_path


def platform_open(path):
    path = os.path.abspath(path)

    system = platform.system()

    # TODO move this to an explicit file for handling os specific operations
    if system == "Windows":
        os.startfile(path)
    elif system == "Linux":
        subprocess.Popen(["xdg-open", path])
    else:
        raise OSError("Unsupported operating system: " + system)

win32_window_size = True

docsFolder = directories.USER
iniFile = directories.INI_FILE


# TODO treat these as "stock" filters
# TODO allow these filters to be configured as hidden individually per filter
# TODO make a separate directory where custom filters can be added
filtersDir = directories.FILTERS
if filtersDir not in [s
                      if isinstance(s, str)
                      else s
                      for s in sys.path]:
                          
    sys.path.append(filtersDir)

items.items = items.Items(join(directories.ROOT, "pymclevel", "items.txt"))
