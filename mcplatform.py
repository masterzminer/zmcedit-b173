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

Platform-specific functions, file io
"""

import os
import sys
import traceback
import platform
import subprocess
from pathlib import Path
import config
from config import LastDir
from config_classes import DirectorySetting

import crossfiledialog

enc = sys.getfilesystemencoding()

from albow import request_new_filename, request_old_filename


cmd_name = "Ctrl"
option_name = "Alt"

def askOpenFile(lastDir: DirectorySetting, title: str):
    """
    lastDir: setting to get the initial dir to open from
    """
    # TODO make a method in DirectorySetting for auto updating a file path after a path or file is selected
    initialDir = lastDir.v

    file_types = ["mclevel", "dat", "mine", "mine.gz", "schematic"]

    def _ask_open():
        if config.use_old_file_browser():
            return request_old_filename(file_types, initialDir)

        try:
            return crossfiledialog.open_file(
                title=title,
                start_dir=str(initialDir),
                filter=["*." + f for f in file_types]
            )
        except:
            print("Failed to load os file dialog, falling back to built in gui")
            traceback.print_exc()

            # On an exception, fall back to the built in gui selector
            return request_old_filename(file_types, initialDir)

    file_name = _ask_open()

    if file_name:
        lastDir.set(Path(file_name).parent)

    return file_name


def askSaveSchematic(defaultName: str):
    lastDir = LastDir.schematic

    file_name = askSaveFile(lastDir.v,
                title='Save this schematic...',
                defaultName=defaultName,
                filetype="schematic"
            )

    if file_name:
        lastDir.set(Path(file_name).parent)

    return file_name


def askCreateWorld():
    lastDir = LastDir.world
    initialDir = lastDir.v

    # Find a valid name for a folder that doesn't already exist
    defaultName = name = "Untitled World"
    i = 0
    while (initialDir / name).exists:
        i += 1
        name = defaultName + " " + str(i)

    # Select the directory
    selected = askSaveFile(lastDir.v, title='Name this new world', defaultName=name)
    
    lastDir.set(Path(selected).parent)

    return selected


def askSaveFolder(lastDir: DirectorySetting, title):
    initialDir = lastDir.v

    if config.use_old_file_browser():
        selected = request_old_filename(directory=initialDir, selectDir=True)
    else:
        selected = crossfiledialog.choose_folder(
            start_dir=str(initialDir),
            title=title
        )
    
    if selected is None or selected == "":
        return None
    
    lastDir.set(selected)

    return selected


def askSaveFile(lastDir: DirectorySetting, title: str, defaultName, filetype: str=None):
    initialDir = lastDir.v;

    if config.use_old_file_browser():
        selected_path = request_new_filename(
            prompt=title,
            suffix=("" if filetype is None else ("." + filetype)),
            directory=initialDir,
            filename=defaultName,
        )
    else:
        selected_path = crossfiledialog.save_file(
            start_dir=str(initialDir if defaultName is None else initialDir / defaultName),
            title=title,
        )

        if selected_path is None or selected_path == "":
            return None

        if filetype is not None:
            selected_path += "." + filetype

    if selected_path is not None:
        lastDir.set(Path(selected_path).parent)

    return selected_path


def platform_open(path: Path):
    return os_ops.open_file(path)



class OS():
    """
    Base class for handling operating system specific processes
    """

    def __init__(self, system_name):
        self.system_name = system_name
        """
        Name of the operating system
        """

    def handle_init(self):
        """
        Called when MC Edit starts, do any needed additional initializing. Can do nothing if nothing extra is needed
        """
        pass


    def open_file(self, path: Path):
        """
        Open the given file using the os native application

        path: The absolute path to the file to open
        """
        print(f"Opening files is not implemented for this os, cannot open path {path}")

class LinuxHandler(OS):
    def open_file(self, path: Path):
        subprocess.Popen(["xdg-open", path])


class MacHandler(OS):
    def open_file(self, path: Path):
        subprocess.Popen(["open", path])

class WindowsHandler(OS):
    def handle_init(self):
        # Inherited from the original fork, "weird fix"
        try:
            from OpenGL.platform import win32
            win32
        except Exception:
            pass
        pass

    def open_file(self, path: Path):
        os.startfile(path)

class UnknownHandler(OS):
    def handle_init(self):
        print("Failed to identify operating system or operating system not supported, some actions may not work")


def find_os_handler():
    system = platform.system()

    if system == "Linux":
        return LinuxHandler(system)
    if system == "Darwin":
        return MacHandler(system)
    elif system == "Windows":
        return WindowsHandler(system)
    else:
        print(f"Unknown operating system: {system}")
        return UnknownHandler(system)


os_ops = find_os_handler()