from __future__ import annotations

#!/usr/bin/env python
# -*- coding: utf8 -*_
"""
mcedit.py

Startup, main menu, keyboard configuration, automatic updating.
"""

# Explicitly set up arguments before doing much else
import arguments

# Hide the default pygame message
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pygame import display, key, rect


import OpenGL
import sys
# TODO move this to the formal arguments module
if "-debug" not in sys.argv:
    OpenGL.ERROR_CHECKING = False

import albow
from albow.dialogs import Dialog
from albow.openglwidgets import GLViewport
from albow.root import RootWidget, schedule as albow_schedule
from config import LastDir, Keys, Controls, Settings, RecentWorlds, save_config
import directories
import functools
from glbackground import Panel
import glutils
import leveleditor
import logging
import mceutils
import mcplatform
from mcplatform import platform_open
import numpy


from OpenGL import GL
import os.path
import pygame
import pymclevel
import release
import sys
import traceback
import importlib
from pymclevel.infiniteworld import MCBetaLevel
from pymclevel.material import materials
from mceutils import FilterControls
from typing import Literal

MCBetaLevel.loadedChunkLimit = 0

ESCAPE = '\033'


class FileOpener(albow.Widget):
    is_gl_container = True

    def __init__(self, mcedit: MCEdit, *args, **kwargs):
        kwargs['rect'] = mcedit.rect
        albow.Widget.__init__(self, *args, **kwargs)
        self.anchor = 'tlbr'
        self.mcedit = mcedit
        self.contentRow = None
        self.reset_content_row()

    def reset_content_row(self):
        helpColumn = []

        label = albow.Label(f"{Keys.forward} {Keys.left} {Keys.back} {Keys.right} {Keys.up} {Keys.down}".upper() + " to move")
        label.anchor = 'whrt'
        label.align = 'r'
        helpColumn.append(label)

        def addHelp(text):
            label = albow.Label(text)
            label.anchor = 'whrt'
            label.align = "r"
            helpColumn.append(label)

        addHelp(f"{Keys.brake.v.upper()} to slow down")
        addHelp("Right-click to toggle camera control")
        addHelp("Mousewheel to control tool distance")
        addHelp("Hold SHIFT to move along a major axis")
        addHelp("Hold ALT for details")

        helpColumn = albow.Column(helpColumn, align="r")
        helpColumn.topright = self.topright
        helpColumn.anchor = "whrt"
        self.add(helpColumn)

        infoButtonsColumn = self.mcedit.makeInfoButtonsColumn()
        infoButtonsColumn.anchor = 'whrb'
        infoButtonsColumn.bottomright = self.bottomright
        self.add(infoButtonsColumn)

        keysColumn = [albow.Label("")]
        buttonsColumn = [leveleditor.ControlPanel.getHeader()]

        short_names = []
        for world in self.mcedit.recentWorlds():
            shortname = os.path.basename(world)
            try:
                if pymclevel.MCBetaLevel.isLevel(world):
                    lev = pymclevel.MCBetaLevel(world)
                    shortname = lev.LevelName
                    if lev.LevelName != lev.displayName:
                        shortname = u"{0} ({1})".format(lev.LevelName, lev.displayName)
            except Exception as e:
                logging.warning(
                    'Couldn\'t get name from recent world: {0!r}'.format(e))

            if shortname == "level.dat":
                shortname = os.path.basename(os.path.dirname(world))

            if len(shortname) > 40:
                shortname = shortname[:37] + "..."
            short_names.append(shortname)

        hotkeys = ([('N', 'Create New World', self.createNewWorld),
            ('O', 'Open a level...', self.promptOpenAndLoad)] + [
            ('F{0}'.format(i + 1), short_names[i], self.createLoadButtonHandler(world))
            for i, world in enumerate(self.mcedit.recentWorlds())])

        commandRow = mceutils.HotkeyColumn(hotkeys, keysColumn, buttonsColumn)
        commandRow.anchor = 'lrh'

        sideColumn = self.mcedit.makeSideColumn(reset_parent=self.reset_content_row)
        sideColumn.anchor = 'wh'

        if self.contentRow:
            self.remove(self.contentRow)

        contentRow = albow.Row((commandRow, albow.Label("      "), sideColumn))
        contentRow.center = self.center
        contentRow.anchor = "rh"
        self.add(contentRow)
        self.contentRow = contentRow
        self.sideColumn = sideColumn

    def gl_draw_self(self, root, offset):
        self.mcedit.editor.drawStars()

    def idle_event(self, evt):
        self.mcedit.editor.doWorkUnit()

    def key_down(self, evt):
        keyname = key.name(evt.key)
        if keyname == 'f4' and (key.get_mods() & (pygame.KMOD_ALT | pygame.KMOD_LALT | pygame.KMOD_RALT)):
            raise SystemExit
        if keyname in ('f1', 'f2', 'f3', 'f4', 'f5'):
            self.mcedit.loadRecentWorldNumber(int(keyname[1]))
        if keyname == "o":
            return self.promptOpenAndLoad()
        if keyname == "n":
            self.createNewWorld()

    def promptOpenAndLoad(self):
        try:
            filename = mcplatform.askOpenFile(LastDir.world, "Select a world...")

            # Get rid of the key events that happened while waiting for the file
            pygame.event.clear()

            if filename:
                self.mcedit.loadFile(filename)
                return True
        except Exception as e:
            traceback.print_exc()
            logging.error('Error during promptOpenAndLoad: {0!r}'.format(e))

    def createNewWorld(self):
        self.parent.createNewWorld()

    def createLoadButtonHandler(self, filename):
        return lambda: self.mcedit.loadFile(filename)


class KeyConfigPanel(Dialog):
    keyConfigKeys = [
        "<Movement Controls>",
        "Forward",
        "Back",
        "Left",
        "Right",
        "Up",
        "Down",
        "Brake",
        "",
        "<Camera Controls>",
        "Pan Left",
        "Pan Right",
        "Pan Up",
        "Pan Down",
        "",
        "<Tool Controls>",
        "Rotate",
        "Roll",
        "Flip",
        "Mirror",
        "Swap",
        "Increase Reach",
        "Decrease Reach",
        "Reset Reach",
    ]

    presets = {"WASD": [
        ("Forward", "w"),
        ("Back", "s"),
        ("Left", "a"),
        ("Right", "d"),
        ("Up", "q"),
        ("Down", "z"),
        ("Brake", "space"),

        ("Rotate", "e"),
        ("Roll", "r"),
        ("Flip", "f"),
        ("Mirror", "g"),
        ("Swap", "x"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ],
    "Arrows": [
        ("Forward", "up"),
        ("Back", "down"),
        ("Left", "left"),
        ("Right", "right"),
        ("Up", "page up"),
        ("Down", "page down"),
        ("Brake", "space"),

        ("Rotate", "home"),
        ("Roll", "end"),
        ("Flip", "insert"),
        ("Mirror", "delete"),
        ("Swap", "\\"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ],
    "Numpad": [
        ("Forward", "[8]"),
        ("Back", "[5]"),
        ("Left", "[4]"),
        ("Right", "[6]"),
        ("Up", "[9]"),
        ("Down", "[3]"),
        ("Brake", "[0]"),

        ("Rotate", "[-]"),
        ("Roll", "[+]"),
        ("Flip", "[/]"),
        ("Mirror", "[*]"),
        ("Swap", "[.]"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ]}

    selectedKeyIndex = 0

    def __init__(self):
        Dialog.__init__(self)
        keyConfigTable = albow.TableView(columns=[albow.TableColumn("Command", 400, "l"), albow.TableColumn("Assigned Key", 150, "r")])
        keyConfigTable.num_rows = lambda: len(self.keyConfigKeys)
        keyConfigTable.row_data = self.getRowData
        keyConfigTable.row_is_selected = lambda x: x == self.selectedKeyIndex
        keyConfigTable.click_row = self.selectTableRow
        tableWidget = albow.Widget()
        tableWidget.add(keyConfigTable)
        tableWidget.shrink_wrap()

        self.keyConfigTable = keyConfigTable

        buttonRow = (albow.Button("Assign Key...", action=self.askAssignSelectedKey),
                     albow.Button("Done", action=self.dismiss))

        buttonRow = albow.Row(buttonRow)

        choiceButton = mceutils.ChoiceButton(["WASD", "Arrows", "Numpad"], choose=self.choosePreset)
        # TODO how is this meant to work?
        if Keys.forward.v == "up":
            choiceButton.selectedChoice = "Arrows"
        if Keys.forward.v == "[8]":
            choiceButton.selectedChoice = "Numpad"

        choiceRow = albow.Row((albow.Label("Presets: "), choiceButton))
        self.choiceButton = choiceButton

        col = albow.Column((tableWidget, choiceRow, buttonRow))
        self.add(col)
        self.shrink_wrap()

    def choosePreset(self):
        preset = self.choiceButton.selectedChoice
        key_pairs = self.presets[preset]
        for configKey, key in key_pairs:
            Keys.set(configKey, key)

    def getRowData(self, i):
        configKey = self.keyConfigKeys[i]
        if self.isConfigKey(configKey):
            key = Keys.get(configKey)
        else:
            key = ""
        return configKey, key

    def isConfigKey(self, configKey):
        return not (len(configKey) == 0 or configKey[0] == "<")

    def selectTableRow(self, i, evt):
        self.selectedKeyIndex = i
        if evt.num_clicks == 2:
            self.askAssignSelectedKey()

    def askAssignSelectedKey(self):
        self.askAssignKey(self.keyConfigKeys[self.selectedKeyIndex])

    def askAssignKey(self, configKey, labelString=None):
        if not self.isConfigKey(configKey):
            return

        panel = Panel()
        panel.bg_color = (0.5, 0.5, 0.6, 1.0)

        if labelString is None:
            labelString = "Press a key to assign to the action \"{0}\"\n\nPress ESC to cancel.".format(configKey)
        label = albow.Label(labelString)
        panel.add(label)
        panel.shrink_wrap()

        def panelKeyDown(evt):
            keyname = key.name(evt.key)
            panel.dismiss(keyname)

        def panelMouseDown(evt):
            button = leveleditor.remapMouseButton(evt.button)
            if button > 2:
                keyname = "mouse{0}".format(button)
                panel.dismiss(keyname)

        panel.key_down = panelKeyDown
        panel.mouse_down = panelMouseDown

        keyname = panel.present()
        if keyname != "escape":
            occupiedKeys = [(v, k) for (k, v) in Keys.get_all() if v == keyname]
            old_key = Keys.get(configKey)
            Keys.set(configKey, keyname)
            for keyname, setting in occupiedKeys:
                if self.askAssignKey(setting,
                                     "The key {0} is no longer bound to {1}.\n"
                                     "Press a new key for the action \"{1}\"\n\n"
                                     "Press ESC to cancel."
                                     .format(keyname, setting)):
                    Keys.set(configKey, old_key)
                    return True
        else:
            return True


class GraphicsPanel(Panel):
    def __init__(self, mcedit):
        Panel.__init__(self)

        self.mcedit = mcedit

        fieldOfViewRow = mceutils.FloatInputRow("Field of View: ",
            setting=Settings.fov, width=100, min=25, max=120)

        targetFPSRow = mceutils.IntInputRow("Target FPS: ",
            setting=Settings.target_fps, width=100, min=1, max=600)

        bufferLimitRow = mceutils.IntInputRow("Vertex Buffer Limit (MB): ", setting=Settings.vertex_buffer_limit, width=100, min=0)

        fastLeavesRow = mceutils.CheckBoxLabel("Fast Leaves",
            setting=Settings.fast_leaves,
            tooltipText="Leaves are solid, like Minecraft's 'Fast' graphics")

        roughGraphicsRow = mceutils.CheckBoxLabel("Rough Graphics",
            setting=Settings.rough_graphics,
            tooltipText="All blocks are drawn the same way (overrides 'Fast Leaves')")

        enableMouseLagRow = mceutils.CheckBoxLabel("Enable Mouse Lag",
            setting=Settings.enable_mouse_lag,
            tooltipText="Enable choppy mouse movement for faster loading.")

        settingsColumn = albow.Column((fastLeavesRow,
                                  roughGraphicsRow,
                                  enableMouseLagRow,
                                  fieldOfViewRow,
                                  targetFPSRow,
                                  bufferLimitRow,
                                  ), align='r')

        settingsColumn = albow.Column((albow.Label("Settings"),
                                 settingsColumn))

        settingsRow = albow.Row((settingsColumn,))

        optionsColumn = albow.Column((settingsRow, albow.Button("OK", action=mcedit.removeGraphicOptions)))
        self.add(optionsColumn)
        self.shrink_wrap()

    def _reloadTextures(self, pack):
        if hasattr(pymclevel.materials, "terrainTexture"):
            self.mcedit.displayContext.loadTextures()

class OptionsPanel(Dialog):
    anchor = 'wh'

    def __init__(self, mcedit):
        Dialog.__init__(self)

        self.mcedit = mcedit

        autoBrakeRow = mceutils.CheckBoxLabel("Autobrake",
            setting=Controls.auto_brake,
            tooltipText="Apply brake when not pressing movement keys")

        swapAxesRow = mceutils.CheckBoxLabel("Swap Axes Looking Down",
            setting=Controls.swap_axes,
            tooltipText="Change the direction of the Forward and Backward keys when looking down")

        cameraAccelRow = mceutils.FloatInputRow("Camera Acceleration: ",
            setting=Controls.camera_acceleration, width=100, min=5.0)

        cameraDragRow = mceutils.FloatInputRow("Camera Drag: ",
            setting=Controls.camera_drag, width=100, min=1.0)

        cameraMaxSpeedRow = mceutils.FloatInputRow("Camera Max Speed: ",
            setting=Controls.camera_max_speed, width=100, min=1.0)

        cameraBrakeSpeedRow = mceutils.FloatInputRow("Camera Braking Speed: ",
            setting=Controls.camera_breaking_speed, width=100, min=1.0)

        mouseSpeedRow = mceutils.FloatInputRow("Mouse Speed: ", setting=Controls.mouse_speed, width=100, min=0.1, max=20.0)

        invertRow = mceutils.CheckBoxLabel("Invert Mouse",
            setting=Controls.invert_mouse_pitch,
            tooltipText="Reverse the up and down motion of the mouse.")
        
        classicMouseRow = mceutils.CheckBoxLabel("Classic Mouse",
            setting=Settings.classic_mouse,
            invert=True,
            tooltipText="Use the mouse pointer from the original version of MC Edit")
           
        centerMouseFixRow = mceutils.CheckBoxLabel("Center Mouse",
            setting=Settings.center_mouse_fix,
            tooltipText="While in 3D look mode, replace the mouse with an invisible cursor and force set the mouse to the center of the window during mouse movement. " \
            "This is a band aid fix for scenarios where the mouse being at the edge of a screen can cause unwanted os activations. " \
            "This setting may or may not fix mouse behavior depending on how the os handles the mouse. " \
            "With this disabled, no additional hack fix will be applied, and the mouse will move around the window while staying hidden.")
         
        menuStarsRow = mceutils.CheckBoxLabel("Hide Menu Stars",
            setting=Settings.hide_menu_stars,
            invert=True,
            tooltipText="Hide the stars in the main menu")
        
        oldFileBrowserRow = mceutils.CheckBoxLabel("Old File Browser", setting=Settings.use_old_file_browser,
            tooltipText="Use the built in file browser instead of an os native browser")

        spaceHeightRow = mceutils.IntInputRow("Low Detail Height", setting=Settings.space_height,
            tooltipText="When you are this far above the top of the world, move fast and use low-detail mode")

        blockBufferRow = mceutils.IntInputRow("Block Buffer",
            setting=Settings.block_buffer, min=1,
            tooltipText="Amount of memory used for temporary storage. When more than this is needed, the disk is used instead")

        longDistanceRow = mceutils.CheckBoxLabel("Long-Distance Mode",
            setting=Settings.long_distance_mode,
            tooltipText="Always target the farthest block under the cursor, even in mouse look mode. Shortcut: ALT-Z")

        # TODO make sure fly mode is implemented, seems to nto be
        flyModeRow = mceutils.CheckBoxLabel("Fly Mode",
            setting=Settings.fly_mode,
            tooltipText="Moving forward and backward will not change your altitude in Fly Mode")

        inputs = (
            spaceHeightRow,
            cameraAccelRow,
            cameraDragRow,
            cameraMaxSpeedRow,
            cameraBrakeSpeedRow,
            blockBufferRow,
            mouseSpeedRow,
        )

        options = (
            longDistanceRow,
            flyModeRow,
            autoBrakeRow,
            swapAxesRow,
            invertRow,
            classicMouseRow,
            centerMouseFixRow,
            menuStarsRow,
            oldFileBrowserRow,
        )

        right_col = albow.Column(options, align='r')
        left_col = albow.Column(inputs, align='r')

        optionsColumn = albow.Column((albow.Label("Options"),
                                albow.Row((left_col, right_col), align="t")))

        settingsRow = albow.Row((optionsColumn,))

        optionsColumn = albow.Column((settingsRow, albow.Button("OK", action=self.closeSettings)))

        self.add(optionsColumn)
        self.shrink_wrap()

    def closeSettings(self):
        save_config()
        self.dismiss()


class MCEdit(GLViewport):
    debug_resize = True

    def __init__(self, displayContext, *args):
        ws = displayContext.getWindowSize()
        r = rect.Rect(0, 0, ws[0], ws[1])
        GLViewport.__init__(self, r)
        self.displayContext = displayContext
        self.bg_color = (0, 0, 0, 1)
        self.anchor = 'tlbr'

        self.optionsPanel = OptionsPanel(self)
        self.graphicOptionsPanel = GraphicsPanel(self)

        self.keyConfigPanel = KeyConfigPanel()

        self.reloadEditor()

        self.fileOpener = FileOpener(self)
        self.add(self.fileOpener)

        self.fileOpener.focus()

    editor = None

    def reloadEditor(self):
        importlib.reload(leveleditor)
        level = None

        pos = None

        if self.editor:
            level = self.editor.level
            self.remove(self.editor)
            c = self.editor.mainViewport
            pos, yaw, pitch = c.position, c.yaw, c.pitch

        self.editor = leveleditor.LevelEditor(self)
        self.editor.anchor = 'tlbr'
        if level:
            self.add(self.editor)
            self.editor.gotoLevel(level)
            self.focus_switch = self.editor

            if pos is not None:
                c = self.editor.mainViewport

                c.position, c.yaw, c.pitch = pos, yaw, pitch

    def removeGraphicOptions(self):
        self.removePanel(self.graphicOptionsPanel)

    def removePanel(self, panel):
        if panel.parent:
            panel.set_parent(None)
            if self.editor.parent:
                self.focus_switch = self.editor
            elif self.fileOpener.parent:
                self.focus_switch = self.fileOpener

    def add_right(self, widget):
        w, h = self.size
        widget.centery = h // 2
        widget.right = w
        self.add(widget)

    def showPanel(self, optionsPanel):
        if optionsPanel.parent:
            optionsPanel.set_parent(None)

        optionsPanel.anchor = "whr"
        self.add_right(optionsPanel)
        self.editor.mouseLookOff()

    def showOptions(self):
        self.optionsPanel.present()

    def showGraphicOptions(self):
        self.showPanel(self.graphicOptionsPanel)

    def showKeyConfig(self):
        self.keyConfigPanel.present()

    def loadRecentWorldNumber(self, i):
        worlds = list(self.recentWorlds())
        if i - 1 < len(worlds):
            self.loadFile(worlds[i - 1])

    def removeLevelDat(self, filename):
        if filename.endswith("level.dat"):
            filename = os.path.dirname(filename)
        return filename

    def recentWorlds(self):
        worlds = []
        for recent_world in RecentWorlds.get():
            try:
                worlds.append(self.removeLevelDat(recent_world))
            except Exception:
                traceback.print_exc()

        return list((f for f in worlds if f and os.path.exists(f)))

    def addRecentWorld(self, filename):
        filename = self.removeLevelDat(filename)
        
        # Get the existing worlds
        new_recent_worlds = list(self.recentWorlds())

        # It's already there, do nothing
        if filename in new_recent_worlds:
            return

        # Add the new world to the beginning of the list
        new_recent_worlds.insert(0, filename)
        self.setRecentWorlds(new_recent_worlds)

    def setRecentWorlds(self, worlds):
        RecentWorlds.set([str(s) for s in worlds]);
    
    def makeSideColumn(self, reset_parent):
        items = (
            albow.Button("Keys", action=self.showKeyConfig),
            albow.Button("Graphics", action=self.showGraphicOptions),
            albow.Button("Options", action=self.showOptions),
            FilterControls(reload=reset_parent)
        )

        return albow.Column(items)

    def makeInfoButtonsColumn(self):
        def showLicense():
            platform_open(directories.INSTALL_ROOT / "LICENSE.txt")

        readmePath = directories.INSTALL_ROOT / "README.md"

        column = ([
            albow.Button(
                "zMCEdit-b173 Repo",
                lambda: platform_open("https://github.com/masterzminer/zmcedit-b173")
            ),
            albow.Button(
                "Source of zMCEdit-b173 fork",
                lambda: platform_open("https://github.com/Khroki/mcedit-old/releases/tag/0.1.5")
            ),
            albow.Button(
                "Original MC Edit Repo",
                lambda: platform_open("http://www.github.com/mcedit/mcedit")
            ),
            albow.Button(
                "View Readme",
                lambda: platform_open(readmePath)
            ),
            albow.Button(
                "License",
                showLicense
            ),
            albow.Button(
                "View Install Folder",
                lambda: platform_open(directories.INSTALL_ROOT)
            ),
            albow.Button(
                "View Config Folder",
                lambda: platform_open(directories.CONFIG)
            )
        ])

        return albow.Column(column, align="r")

    def resized(self, dw, dh):
        """
        Handle window resizing events.
        """
        GLViewport.resized(self, dw, dh)

        (w, h) = self.size
        if w == 0 and h == 0:
            # The window has been minimized, no need to draw anything.
            self.editor.renderer.render = False
            return

        if not self.editor.renderer.render:
            self.editor.renderer.render = True

        surf = pygame.display.get_surface()
        assert isinstance(surf, pygame.Surface)
        dw, dh = surf.get_size()

        if w > 0 and h > 0:
            Settings.window_width.set(w)
            Settings.window_height.set(h)
            save_config()

    def loadFile(self, filename, starting_pos=None, starting_look=None, dimension:Literal["overworld","nether"]=None):
        self.removeGraphicOptions()
        if os.path.exists(filename):
            try:
                loaded = self.editor.loadFile(filename, starting_pos, starting_look, dimension)
                if not loaded:
                    return
            except Exception as e:
                traceback.print_exc()
                return None

            self.remove(self.fileOpener)
            self.fileOpener = None
            if self.editor.level:
                self.editor.size = self.size
                self.add(self.editor)
                self.focus_switch = self.editor

    def createNewWorld(self):
        level = self.editor.createNewLevel()
        if level:
            self.remove(self.fileOpener)
            self.editor.size = self.size

            self.add(self.editor)

            self.focus_switch = self.editor
            albow.alert("World created. To expand this infinite world, explore the world in Minecraft or use the Chunk Control tool to add or delete chunks.")

    def removeEditor(self):
        self.remove(self.editor)
        self.fileOpener = FileOpener(self)
        self.add(self.fileOpener)
        self.focus_switch = self.fileOpener

    def confirm_quit(self):
        if self.editor.unsavedEdits:
            result = albow.ask("There are {0} unsaved changes.".format(self.editor.unsavedEdits),
                     responses=["Save and Quit", "Quit", "Cancel"])
            if result == "Save and Quit":
                self.saveAndQuit()
            elif result == "Quit":
                self.justQuit()
            elif result == "Cancel":
                return False
        else:
            raise SystemExit

    def saveAndQuit(self):
        self.editor.saveFile()
        raise SystemExit

    def justQuit(self):
        raise SystemExit

    @classmethod
    def main(self):
        displayContext = GLDisplayContext()

        root_widget = RootWidget(displayContext.display)
        mcedit = MCEdit(displayContext)
        root_widget.displayContext = displayContext
        root_widget.confirm_quit = mcedit.confirm_quit
        root_widget.mcedit = mcedit

        root_widget.add(mcedit)
        root_widget.focus_switch = mcedit
        if 0 == len(materials.yamlDatas):
            albow.alert("Failed to load minecraft.yaml. Check the console window for details.")

        self.root_widget = root_widget

        if Settings.close_minecraft_warning.v:
            answer = albow.ask("Warning: You must close Minecraft completely before editing. Save corruption may result", ["Don't remind me again.", "OK"], default=1, cancel=1)
            if answer == "Don't remind me again.":
                Settings.close_minecraft_warning.set(False)

        save_config()

        # If a world was supplied, load it immediately
        start_world = arguments.LOAD_WORLD
        if start_world:
            if arguments.START_NETHER:
                dimension = "nether"
            elif arguments.START_OVERWORLD:
                dimension = "overworld"
            else:
                dimension = None
            albow_schedule(lambda: mcedit.loadFile(str(start_world), starting_pos=arguments.START_POS, starting_look=arguments.START_LOOK, dimension=dimension))

        while True:
            try:
                root_widget.run()
            except SystemExit:
                save_config()
                mcedit.editor.renderer.discardAllChunks()
                mcedit.editor.deleteAllCopiedSchematics()
                raise
            except MemoryError:
                traceback.print_exc()
                mcedit.editor.handleMemoryError()


def main():
    """
    Setup logging, display, bundled schematics. Handle unclean
    shutdowns.
    """
    # Setup file and stderr logging.
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(directories.LOG_FILE)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    fmt = logging.Formatter(
        '[%(levelname)s][%(lineno)d][%(module)s]:%(message)s'
    )
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    try:
        display.init()
    except pygame.error as e:
        os.environ['SDL_VIDEODRIVER'] = 'directx'
        try:
            display.init()
        except pygame.error:
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            display.init()

    pygame.font.init()

    try:
        MCEdit.main()
    except SystemExit:
        return 0
    except Exception as e:
        logging.error('An unhandled error occurred.', exc_info=True)
        display.quit()
        return 1
    return 0


class GLDisplayContext(object):
    def __init__(self):
        self.reset()

    def getWindowSize(self):
        w, h = (Settings.window_width.v, Settings.window_height.v)
        return max(20, w), max(20, h)

    def displayMode(self):
        displayMode = pygame.OPENGL | pygame.RESIZABLE
        if Settings.double_buffer.v:
            displayMode |= pygame.DOUBLEBUF
        return displayMode

    def reset(self):
        pygame.key.set_repeat(500, 100)

        try:
            display.gl_set_attribute(pygame.GL_SWAP_CONTROL, Settings.vsync.v)
        except Exception as e:
            logging.warning('Unable to set vertical sync: {0!r}'.format(e))

        display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

        d = display.set_mode(self.getWindowSize(), self.displayMode())
        try:
            pygame.scrap.init()
        except:
            logging.warning('PyGame clipboard integration disabled.')

        display.set_caption(release.NAME + ' ~ ' + release.VERSION, release.NAME)

        try:
            icon_path = directories.ASSETS / 'favicon.png'
            icon_file = open(icon_path, 'rb')
            icon = pygame.image.load(icon_file, 'favicon.png')
            display.set_icon(icon)
        except Exception as e:
            logging.warning('Unable to set icon: {0!r}'.format(e))

        self.display = d

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glAlphaFunc(GL.GL_NOTEQUAL, 0)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # textures are 256x256, so with this we can specify pixel coordinates
        GL.glMatrixMode(GL.GL_TEXTURE)
        GL.glScale(1 / 256., 1 / 256., 1 / 256.)

        self.loadTextures()

    def getTerrainTexture(self, level):
        return self.terrainTextures

    def loadTextures(self):
        self.terrainTextures = None

        def makeTerrainTexture(mats):
            w, h = 1, 1
            tex_image = numpy.zeros((w, h, 4), dtype='uint8')
            tex_image[:] = 127, 127, 127, 255

            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGBA8,
                w,
                h,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                tex_image
            )

        textures = (
            (materials, 'terrain.png'),
        )

        for mats, matFile in textures:
            try:
                tex = mceutils.loadTerrainTexture()
                self.terrainTextures = tex
            except Exception as e:
                logging.warning(
                    'Unable to load terrain from {0}, using flat colors.'
                    'Error was: {1!r}'.format(matFile, e)
                )
                self.terrainTextures = glutils.Texture(
                    functools.partial(makeTerrainTexture, mats)
                )
            mats.terrainTexture = self.terrainTextures


mcplatform.os_ops.handle_init()

if __name__ == "__main__":
    sys.exit(main())
