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


if sys.platform == "win32":
    import platform
    if platform.architecture()[0] == "32bit":
        plat = "win32"
    if platform.architecture()[0] == "64bit":
        plat = "win-amd64"
    sys.path.append(join(directories.dataDir, "pymclevel", "build", "lib." + plat + "-2.6").encode(enc))

os.environ["YAML_ROOT"] = join(directories.dataDir, "pymclevel")

from pygame import display

from albow import request_new_filename, request_old_filename
from pymclevel import saveFileDir
from pymclevel import items

import shutil


# for k,v in os.environ.iteritems():
#    try:
#        os.environ[k] = v.decode(sys.getfilesystemencoding())
#    except:
#        continue
if sys.platform == "win32":
    try:
        from win32 import win32gui
        from win32 import win32api

        from win32.lib import win32con
    except ImportError:
        import win32gui
        import win32api

        import win32con

    try:
        import win32com.client
        from win32com.shell import shell, shellcon  # @UnresolvedImport
    except:
        pass

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
        initialDir = lastSchematicsDir or fixedSchematicsDir

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


def documents_folder():
    docsFolder = None

    if sys.platform == "win32":
        try:
            objShell = win32com.client.Dispatch("WScript.Shell")
            docsFolder = objShell.SpecialFolders("MyDocuments")

        except Exception as e:
            print(e)
            try:
                docsFolder = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
            except Exception as e:
                userprofile = os.environ['USERPROFILE'].decode(sys.getfilesystemencoding())
                docsFolder = os.path.join(userprofile, "Documents")

    else:
        docsFolder = os.path.expanduser(u"~/.mcedit")
    try:
        os.mkdir(docsFolder)
    except:
        pass

    return docsFolder


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

ini = u"mcedit.ini"
parentDir = dirname(directories.dataDir)
docsFolder = documents_folder()
fixedConfigFilePath = os.path.join(docsFolder, ini)
fixedSchematicsDir = os.path.join(docsFolder, u"MCEdit-schematics")
configFilePath=fixedConfigFilePath

def move_displace(src, dst):
    dstFolder = os.path.basename(os.path.dirname(dst))
    if not os.path.exists(dst):

        print("Moving {0} to {1}".format(os.path.basename(src), dstFolder))
        shutil.move(src, dst)
    else:
        old_dst = dst + ".old"
        i = 0
        while os.path.exists(old_dst):
            old_dst = dst + ".old" + str(i)
            i += 1

        print("{0} already found in {1}! Renamed it to {2}.".format(os.path.basename(src), dstFolder, dst))
        os.rename(dst, old_dst)
        shutil.move(src, dst)



filtersDir = os.path.join(directories.dataDir, "filters")
if filtersDir not in [s
                      if isinstance(s, str)
                      else s
                      for s in sys.path]:
                          
    sys.path.append(filtersDir)

items.items = items.Items(join(directories.dataDir, "pymclevel", "items.txt"))
