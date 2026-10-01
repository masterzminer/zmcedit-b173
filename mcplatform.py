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

import crossfiledialog

enc = sys.getfilesystemencoding()

os.environ["YAML_ROOT"] = join(directories.ROOT, "pymclevel")

from pygame import display

from albow import request_new_filename, request_old_filename
from pymclevel import saveFileDir
from pymclevel import items


AppKit = None

lastSchematicsDir = None
lastSaveDir = None
cmd_name = "Ctrl"
option_name = "Alt"

def askOpenFile(title='Select a Minecraft level...', schematics=False):
    file_types = ["mclevel", "dat", "mine", "mine.gz"]

    global lastSchematicsDir, lastSaveDir
    initialDir = lastSaveDir or saveFileDir
    if schematics:
        initialDir = lastSchematicsDir or baseSchematicsDir

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


def askSaveSchematic(initialDir, displayName, fileFormat):
    return askSaveFile(initialDir,
                title='Save this schematic...',
                defaultName=displayName + "." + fileFormat,
                filetype='Minecraft Schematics (*.{0})\0*.{0}\0\0'.format(fileFormat),
                suffix=fileFormat,
                )


def askCreateWorld(initialDir):
    defaultName = name = "Untitled World"
    i = 0
    while exists(join(initialDir, name)):
        i += 1
        name = defaultName + " " + str(i)

    return askSaveFile(initialDir,
                title='Name this new world.',
                defaultName=name,
                filetype='Minecraft World\0*.*\0\0',
                suffix="",
                )


def askSaveFile(initialDir, title, defaultName, filetype, suffix):
    if sys.platform == "win32":
        try:
            (filename, customfilter, flags) = win32gui.GetSaveFileNameW(
                hwndOwner=display.get_wm_info()['window'],
                InitialDir=initialDir,
                Flags=win32con.OFN_EXPLORER | win32con.OFN_NOCHANGEDIR | win32con.OFN_OVERWRITEPROMPT,
                File=defaultName,
                DefExt=suffix,
                Title=title,
                Filter=filetype,
                )
        except Exception as e:
            print("Error getting file name: ", e)
            return

        try:
            filename = filename[:filename.index('\0')]
            filename = filename.decode(sys.getfilesystemencoding())
        except:
            pass

    else:
        filename = request_new_filename(prompt=title,
                                        suffix=("." + suffix) if suffix else "",
                                        directory=initialDir,
                                        filename=defaultName,
                                        pathname=None)

    return filename



# TODO probably use a library to abstract this out
def platform_open(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
            # os.system('start ' + path + '\'')
        else:
            os.system('xdg-open "' + path + '"')

    except Exception as e:
        print("platform_open failed on {0}: {1}".format(sys.platform, e))

win32_window_size = True

docsFolder = directories.USER
iniFile = directories.INI_FILE
baseSchematicsDir = directories.USER_SCHEMATICS


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
