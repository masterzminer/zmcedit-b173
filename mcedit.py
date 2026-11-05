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
if arguments.DEBUG:
    OpenGL.ERROR_CHECKING = False

import albow
from albow.dialogs import Dialog
from albow.openglwidgets import GLViewport
from albow.root import RootWidget, schedule as albow_schedule
from config import LastDir, Keys, WorldKeys, Controls, Settings, RecentWorlds, save_config
from config_classes import Setting
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

        def build_world_buttons():
            buttons = []
            
            for i, world in enumerate(self.mcedit.recentWorlds()):
                world_key = WorldKeys.get_from_index(i)
                if world_key is None:
                    continue
                # Each button is the display for the hot key, the world name, and the button itself to load the world
                buttons.append((f'{world_key.upper()}', short_names[i], self.createLoadButtonHandler(world)))
                            
            return buttons
        
        hotkeys = ([
                (Keys.new_level.v, 'Create New World', self.createNewWorld),
                (Keys.open_level.v, 'Open a level...', self.promptOpenAndLoad)
            ] + 
            build_world_buttons()
        )

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
        world_hotkey_index = WorldKeys.list_index_from_value(keyname)
        if world_hotkey_index is not None:
            self.mcedit.loadRecentWorldIndex(world_hotkey_index)
        if keyname == Keys.open_level.v:
            return self.promptOpenAndLoad()
        if keyname == Keys.new_level.v:
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
    display_names = {
        Keys.forward.name: "Forward",
        Keys.back.name: "Back",
        Keys.left.name: "Left",
        Keys.right.name: "Right",
        Keys.up.name: "Up",
        Keys.down.name: "Down",
        Keys.brake.name: "Brake",
        Keys.pan_left.name: "Pan Left",
        Keys.pan_right.name: "Pan Right",
        Keys.pan_up.name: "Pan Up",
        Keys.pan_down.name: "Pan Down",
        Keys.rotate.name: "Rotate",
        Keys.roll.name: "Roll",
        Keys.flip.name: "Flip",
        Keys.mirror.name: "Mirror",
        Keys.swap.name: "Swap",
        Keys.reach_increase.name: "Increase Reach",
        Keys.reach_decrease.name: "Decrease Reach",
        Keys.reach_reset.name: "Reset Reach",
    }

    keyConfigKeys = [
        "<Movement Controls>",
        Keys.forward,
        Keys.back,
        Keys.left,
        Keys.right,
        Keys.up,
        Keys.down,
        Keys.brake,
        "",
        "<Camera Controls>",
        Keys.pan_left,
        Keys.pan_right,
        Keys.pan_up,
        Keys.pan_down,
        "",
        "<Tool Controls>",
        Keys.rotate,
        Keys.roll,
        Keys.flip,
        Keys.mirror,
        Keys.swap,
        Keys.reach_increase,
        Keys.reach_decrease,
        Keys.reach_reset,
    ]

    presets = {
        "WASD": [
            (Keys.forward, "w"),
            (Keys.back, "s"),
            (Keys.left, "a"),
            (Keys.right, "d"),
            (Keys.up, "q"),
            (Keys.down, "z"),
            (Keys.brake, "space"),

            (Keys.rotate, "e"),
            (Keys.roll, "r"),
            (Keys.flip, "f"),
            (Keys.mirror, "g"),
            (Keys.swap, "x"),
            (Keys.reach_increase, "mouse4"),
            (Keys.reach_decrease, "mouse5"),
            (Keys.reach_reset, "mouse3"),
        ],
        "Arrows": [
            (Keys.forward, "up"),
            (Keys.back, "down"),
            (Keys.left, "left"),
            (Keys.right, "right"),
            (Keys.up, "page up"),
            (Keys.down, "page down"),
            (Keys.brake, "space"),

            (Keys.rotate, "home"),
            (Keys.roll, "end"),
            (Keys.flip, "insert"),
            (Keys.mirror, "delete"),
            (Keys.swap, "\\"),
            (Keys.reach_increase, "mouse4"),
            (Keys.reach_decrease, "mouse5"),
            (Keys.reach_reset, "mouse3"),
        ],
        "Numpad": [
            (Keys.forward, "[8]"),
            (Keys.back, "[5]"),
            (Keys.left, "[4]"),
            (Keys.right, "[6]"),
            (Keys.up, "[9]"),
            (Keys.down, "[3]"),
            (Keys.brake, "[0]"),

            (Keys.rotate, "[-]"),
            (Keys.roll, "[+]"),
            (Keys.flip, "[/]"),
            (Keys.mirror, "[*]"),
            (Keys.swap, "[.]"),
            (Keys.reach_increase, "mouse4"),
            (Keys.reach_decrease, "mouse5"),
            (Keys.reach_reset, "mouse3"),
        ]
    }

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

        choiceButton = mceutils.ChoiceButton(list(self.presets.keys()), choose=self.choosePreset)

        choiceRow = albow.Row((albow.Label("Presets: "), choiceButton))
        self.choiceButton = choiceButton

        col = albow.Column((tableWidget, choiceRow, buttonRow))
        self.add(col)
        self.shrink_wrap()

    def choosePreset(self):
        preset = self.choiceButton.selectedChoice
        key_pairs = self.presets[preset]
        for setting, value in key_pairs:
            setting.set(value)
        save_config()

    def getRowData(self, i):
        configKeyData = self.keyConfigKeys[i]
        if isinstance(configKeyData, str):
            display = configKeyData
            key = ""
        else:
            display = self.display_names[configKeyData.name]
            name = configKeyData.v
            key = name.upper() if len(name) == 1 else name
        return display, key

    def selectTableRow(self, i, evt):
        self.selectedKeyIndex = i
        if evt.num_clicks == 2:
            self.askAssignSelectedKey()

    def askAssignSelectedKey(self):
        self.askAssignKey(self.keyConfigKeys[self.selectedKeyIndex])

    def askAssignKey(self, keyConfig, labelString=None):
        if not isinstance(keyConfig, Setting):
            return
        keySetting = keyConfig

        panel = Panel()
        panel.bg_color = (0.5, 0.5, 0.6, 1.0)

        if labelString is None:
            labelString = f"Press a key to assign to the action \"{keySetting}\"\n\nPress ESC to cancel."
        label = albow.Label(labelString)
        panel.add(label)
        panel.shrink_wrap()

        def panelKeyDown(evt):
            keyname = key.name(evt.key)
            panel.dismiss(keyname)

        def panelMouseDown(evt):
            button = leveleditor.remapMouseButton(evt.button)
            if button > 2:
                keyname = f"mouse{button}"
                panel.dismiss(keyname)

        panel.key_down = panelKeyDown
        panel.mouse_down = panelMouseDown

        keyname = panel.present()
        if keyname != "escape":
            occupiedKeys = [entry for entry in Keys.get_settings() if entry[1].v == keyname]
            old_key = keySetting.get()
            keySetting.set(keyname)
            for keyname, setting in occupiedKeys:
                # Skip if it's the same setting as the one being set
                if setting.name == keySetting.name:
                    continue

                display_key = self.display_names[setting.name]
                if self.askAssignKey(setting, f'The key "{display_key}" is no longer bound to "{setting}".\nPress a new key for the action "{display_key}"\n\n Press ESC to cancel.'):
                    keySetting.set(old_key)
                    return True
        else:
            save_config()
            return True


class GraphicsPanel(Panel):
    def __init__(self, mcedit):
        Panel.__init__(self)

        self.mcedit = mcedit

        fieldOfViewRow = mceutils.FloatInputRow("Field of View: ", ref=Settings.fov, width=100, min=25, max=120)

        targetFPSRow = mceutils.IntInputRow("Target FPS: ", ref=Settings.target_fps, width=100, min=1, max=600)

        bufferLimitRow = mceutils.IntInputRow("Vertex Buffer Limit (MB): ", ref=Settings.vertex_buffer_limit, width=100, min=0)

        fastLeavesRow = mceutils.CheckBoxLabel("Fast Leaves", ref=Settings.fast_leaves,
            tooltipText="Leaves are solid, like Minecraft's 'Fast' graphics")

        roughGraphicsRow = mceutils.CheckBoxLabel("Rough Graphics", ref=Settings.rough_graphics,
            tooltipText="All blocks are drawn the same way (overrides 'Fast Leaves')")

        enableMouseLagRow = mceutils.CheckBoxLabel("Enable Mouse Lag", ref=Settings.enable_mouse_lag,
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

        autoBrakeRow = mceutils.CheckBoxLabel("Autobrake", ref=Controls.auto_brake,
            tooltipText="Apply brake when not pressing movement keys")

        swapAxesRow = mceutils.CheckBoxLabel("Swap Axes Looking Down", ref=Controls.swap_axes,
            tooltipText="Change the direction of the Forward and Backward keys when looking down")

        cameraAccelRow = mceutils.FloatInputRow("Camera Acceleration: ", ref=Controls.camera_acceleration, width=100, min=5.0)

        cameraDragRow = mceutils.FloatInputRow("Camera Drag: ", ref=Controls.camera_drag, width=100, min=1.0)

        cameraMaxSpeedRow = mceutils.FloatInputRow("Camera Max Speed: ", ref=Controls.camera_max_speed, width=100, min=1.0)

        cameraBrakeSpeedRow = mceutils.FloatInputRow("Camera Braking Speed: ", ref=Controls.camera_breaking_speed, width=100, min=1.0)

        mouseSpeedRow = mceutils.FloatInputRow("Mouse Speed: ", ref=Controls.mouse_speed, width=100, min=0.1, max=20.0)

        invertRow = mceutils.CheckBoxLabel("Invert Mouse", ref=Controls.invert_mouse_pitch,
            tooltipText="Reverse the up and down motion of the mouse.")
        
        classicMouseRow = mceutils.CheckBoxLabel("Classic Mouse", ref=Settings.classic_mouse, invert=True,
            tooltipText="Use the mouse pointer from the original version of MC Edit")
           
        centerMouseFixRow = mceutils.CheckBoxLabel("Center Mouse", ref=Settings.center_mouse_fix,
            tooltipText="While in 3D look mode, replace the mouse with an invisible cursor and force set the mouse to the center of the window during mouse movement. " \
            "This is a band aid fix for scenarios where the mouse being at the edge of a screen can cause unwanted os activations. " \
            "This setting may or may not fix mouse behavior depending on how the os handles the mouse. " \
            "With this disabled, no additional hack fix will be applied, and the mouse will move around the window while staying hidden.")
         
        menuStarsRow = mceutils.CheckBoxLabel("Hide Menu Stars", ref=Settings.hide_menu_stars, invert=True,
            tooltipText="Hide the stars in the main menu")
        
        oldFileBrowserRow = mceutils.CheckBoxLabel("Old File Browser", ref=Settings.use_old_file_browser,
            tooltipText="Use the built in file browser instead of an os native browser")

        spaceHeightRow = mceutils.IntInputRow("Low Detail Height", ref=Settings.space_height,
            tooltipText="When you are this far above the top of the world, move fast and use low-detail mode")

        longDistanceRow = mceutils.CheckBoxLabel("Long-Distance Mode", ref=Settings.long_distance_mode,
            tooltipText="Always target the farthest block under the cursor, even in mouse look mode. Shortcut: ALT-Z")

        flyModeRow = mceutils.CheckBoxLabel("Fly Mode", ref=Settings.fly_mode,
            tooltipText="Moving forward and backward will not change your altitude in Fly Mode")

        inputs = (
            spaceHeightRow,
            cameraAccelRow,
            cameraDragRow,
            cameraMaxSpeedRow,
            cameraBrakeSpeedRow,
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
            self.editor.loadLevel(level)
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

    def loadRecentWorldIndex(self, i):
        worlds = list(self.recentWorlds())
        if i < len(worlds):
            self.loadFile(worlds[i])

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
