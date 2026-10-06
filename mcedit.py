from __future__ import annotations

#!/usr/bin/env python
# -*- coding: utf8 -*_
"""
mcedit.py

Startup, main menu, keyboard configuration, automatic updating.
"""

# Hide the default pygame message
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pygame import display, key, rect


import OpenGL
import sys
if "-debug" not in sys.argv:
    OpenGL.ERROR_CHECKING = False

import albow
from albow.dialogs import Dialog
from albow.openglwidgets import GLViewport
from albow.root import RootWidget
import config
import directories
import functools
from glbackground import Panel
import glutils
import leveleditor
from leveleditor import ControlSettings, Settings
import logging
import mceutils
import mcplatform
from mcplatform import platform_open
import numpy
from pathlib import Path


from OpenGL import GL
import os.path
import pygame
import pymclevel
import release
import sys
import traceback
import importlib
from pymclevel.infiniteworld import MCBetaLevel
from pymclevel.materials import alphaMaterials

MCBetaLevel.loadedChunkLimit = 0

ESCAPE = '\033'


class FileOpener(albow.Widget):
    is_gl_container = True

    def __init__(self, mcedit: MCEdit, *args, **kwargs):
        kwargs['rect'] = mcedit.rect
        albow.Widget.__init__(self, *args, **kwargs)
        self.anchor = 'tlbr'
        self.mcedit = mcedit

        helpColumn = []

        label = albow.Label("{0} {1} {2} {3} {4} {5}".format(
            config.config.get('Keys', 'Forward'),
            config.config.get('Keys', 'Left'),
            config.config.get('Keys', 'Back'),
            config.config.get('Keys', 'Right'),
            config.config.get('Keys', 'Up'),
            config.config.get('Keys', 'Down'),
        ).upper() + " to move")
        label.anchor = 'whrt'
        label.align = 'r'
        helpColumn.append(label)

        def addHelp(text):
            label = albow.Label(text)
            label.anchor = 'whrt'
            label.align = "r"
            helpColumn.append(label)

        addHelp("{0}".format(config.config.get('Keys', 'Brake').upper()) + " to slow down")
        addHelp("Right-click to toggle camera control")
        addHelp("Mousewheel to control tool distance")
        addHelp("Hold SHIFT to move along a major axis")
        addHelp("Hold ALT for details")

        helpColumn = albow.Column(helpColumn, align="r")
        helpColumn.topright = self.topright
        helpColumn.anchor = "whrt"
        self.add(helpColumn)

        infoButtonsColumn = mcedit.makeInfoButtonsColumn()
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

        sideColumn = mcedit.makeSideColumn()
        sideColumn.anchor = 'wh'

        contentRow = albow.Row((commandRow, sideColumn))
        contentRow.center = self.center
        contentRow.anchor = "rh"
        self.add(contentRow)
        self.sideColumn = sideColumn

    def gl_draw_self(self, root, offset):
        #self.mcedit.editor.mainViewport.setPerspective();
        self.mcedit.editor.drawStars()

    def idle_event(self, evt):
        self.mcedit.editor.doWorkUnit()
        #self.invalidate()

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
            filename = mcplatform.askOpenFile()

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
        return lambda: self.mcedit.loadFile(os.path.join(filename, "level.dat"))


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
        if config.config.get("Keys", "Forward") == "up":
            choiceButton.selectedChoice = "Arrows"
        if config.config.get("Keys", "Forward") == "[8]":
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
            config.config.set("Keys", configKey, key)

    def getRowData(self, i):
        configKey = self.keyConfigKeys[i]
        if self.isConfigKey(configKey):
            key = config.config.get("Keys", configKey)
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
            occupiedKeys = [(v, k) for (k, v) in config.config.items("Keys") if v == keyname]
            old_key = config.config.get("Keys", configKey)
            config.config.set("Keys", configKey, keyname)
            for keyname, setting in occupiedKeys:
                if self.askAssignKey(setting,
                                     "The key {0} is no longer bound to {1}.\n"
                                     "Press a new key for the action \"{1}\"\n\n"
                                     "Press ESC to cancel."
                                     .format(keyname, setting)):
                    config.config.set("Keys", configKey, old_key)
                    return True
        else:
            return True


class GraphicsPanel(Panel):
    def __init__(self, mcedit):
        Panel.__init__(self)

        self.mcedit = mcedit

        fieldOfViewRow = mceutils.FloatInputRow("Field of View: ",
            ref=Settings.fov.propertyRef(), width=100, min=25, max=120)

        targetFPSRow = mceutils.IntInputRow("Target FPS: ",
            ref=Settings.targetFPS.propertyRef(), width=100, min=1, max=600)

        bufferLimitRow = mceutils.IntInputRow("Vertex Buffer Limit (MB): ",
            ref=Settings.vertexBufferLimit.propertyRef(), width=100, min=0)

        fastLeavesRow = mceutils.CheckBoxLabel("Fast Leaves",
            ref=Settings.fastLeaves.propertyRef(),
            tooltipText="Leaves are solid, like Minecraft's 'Fast' graphics")

        roughGraphicsRow = mceutils.CheckBoxLabel("Rough Graphics",
            ref=Settings.roughGraphics.propertyRef(),
            tooltipText="All blocks are drawn the same way (overrides 'Fast Leaves')")

        enableMouseLagRow = mceutils.CheckBoxLabel("Enable Mouse Lag",
            ref=Settings.enableMouseLag.propertyRef(),
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
        if hasattr(pymclevel.alphaMaterials, "terrainTexture"):
            self.mcedit.displayContext.loadTextures()

class OptionsPanel(Dialog):
    anchor = 'wh'

    def __init__(self, mcedit):
        Dialog.__init__(self)

        self.mcedit = mcedit

        autoBrakeRow = mceutils.CheckBoxLabel("Autobrake",
            ref=ControlSettings.autobrake.propertyRef(),
            tooltipText="Apply brake when not pressing movement keys")

        swapAxesRow = mceutils.CheckBoxLabel("Swap Axes Looking Down",
            ref=ControlSettings.swapAxes.propertyRef(),
            tooltipText="Change the direction of the Forward and Backward keys when looking down")

        cameraAccelRow = mceutils.FloatInputRow("Camera Acceleration: ",
            ref=ControlSettings.cameraAccel.propertyRef(), width=100, min=5.0)

        cameraDragRow = mceutils.FloatInputRow("Camera Drag: ",
            ref=ControlSettings.cameraDrag.propertyRef(), width=100, min=1.0)

        cameraMaxSpeedRow = mceutils.FloatInputRow("Camera Max Speed: ",
            ref=ControlSettings.cameraMaxSpeed.propertyRef(), width=100, min=1.0)

        cameraBrakeSpeedRow = mceutils.FloatInputRow("Camera Braking Speed: ",
            ref=ControlSettings.cameraBrakingSpeed.propertyRef(), width=100, min=1.0)

        mouseSpeedRow = mceutils.FloatInputRow("Mouse Speed: ",
            ref=ControlSettings.mouseSpeed.propertyRef(), width=100, min=0.1, max=20.0)

        invertRow = mceutils.CheckBoxLabel("Invert Mouse",
            ref=ControlSettings.invertMousePitch.propertyRef(),
            tooltipText="Reverse the up and down motion of the mouse.")

        spaceHeightRow = mceutils.IntInputRow("Low Detail Height",
            ref=Settings.spaceHeight.propertyRef(),
            tooltipText="When you are this far above the top of the world, move fast and use low-detail mode.")

        blockBufferRow = mceutils.IntInputRow("Block Buffer",
            ref=Settings.blockBuffer.propertyRef(), min=1,
            tooltipText="Amount of memory used for temporary storage.  When more than this is needed, the disk is used instead.")

        visibilityCheckRow = mceutils.CheckBoxLabel("Visibility Check",
            ref=Settings.visibilityCheck.propertyRef(),
            tooltipText="Do a visibility check on chunks while loading. May cause a crash.")

        longDistanceRow = mceutils.CheckBoxLabel("Long-Distance Mode",
            ref=Settings.longDistanceMode.propertyRef(),
            tooltipText="Always target the farthest block under the cursor, even in mouse look mode. Shortcut: ALT-Z")

        flyModeRow = mceutils.CheckBoxLabel("Fly Mode",
            ref=Settings.flyMode.propertyRef(),
            tooltipText="Moving forward and backward will not change your altitude in Fly Mode.")

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
            visibilityCheckRow
        )

        right_col = albow.Column(options, align='r')
        left_col = albow.Column(inputs, align='r')

        optionsColumn = albow.Column((albow.Label("Options"),
                                albow.Row((left_col, right_col), align="t")))

        settingsRow = albow.Row((optionsColumn,))

        optionsColumn = albow.Column((settingsRow, albow.Button("OK", action=self.dismiss)))

        self.add(optionsColumn)
        self.shrink_wrap()

    @property
    def blockBuffer(self):
        return Settings.blockBuffer.get() / 1048576

    @blockBuffer.setter
    def blockBuffer(self, val):
        Settings.blockBuffer.set(int(val * 1048576))


class MCEdit(GLViewport):
    debug_resize = True

    def __init__(self, displayContext, *args):
        ws = displayContext.getWindowSize()
        r = rect.Rect(0, 0, ws[0], ws[1])
        GLViewport.__init__(self, r)
        self.displayContext = displayContext
        self.bg_color = (0, 0, 0, 1)
        self.anchor = 'tlbr'

        if not config.config.has_section("Recent Worlds"):
            config.config.add_section("Recent Worlds")
            self.setRecentWorlds([""] * 5)

        if not config.config.has_section("Directories"):
            config.config.add_section("Directories")
            home = Path.home()
            config.updateLastDataDir(home)
            config.updateLastSchematicDir(home)

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
            self.loadFile(os.path.join(worlds[i - 1], "level.dat"))

    numRecentWorlds = 5

    def removeLevelDat(self, filename):
        if filename.endswith("level.dat"):
            filename = os.path.dirname(filename)
        return filename

    def recentWorlds(self):
        worlds = []
        for i in range(self.numRecentWorlds):
            if config.config.has_option("Recent Worlds", str(i)):
                try:
                    filename = config.config.get("Recent Worlds", str(i))
                    if not isinstance(filename, str):
                        filename = filename.decode("utf-8")
                    worlds.append(self.removeLevelDat(filename))
                except Exception as e:
                    traceback.print_exc()

        return list((f for f in worlds if f and os.path.exists(f)))

    def addRecentWorld(self, filename):
        filename = self.removeLevelDat(filename)
        rw = list(self.recentWorlds())
        if filename in rw:
            return
        rw = [filename] + rw[:self.numRecentWorlds - 1]
        self.setRecentWorlds(rw)

    def setRecentWorlds(self, worlds):
        for i, filename in enumerate(worlds):
            config.config.set("Recent Worlds", str(i), filename)
            
    def makeSideColumn(self):
        hotkeys = ([
            ("",
                "Keys",
                self.showKeyConfig
            ),
            ("",
                "Graphics",
                self.showGraphicOptions
            ),
            ("",
                "Options",
                self.showOptions
            ),
        ])

        return mceutils.HotkeyColumn(hotkeys)

    def makeInfoButtonsColumn(self):
        def showLicense():
            platform_open(directories.READ_ROOT / "LICENSE.txt")

        readmePath = directories.READ_ROOT / "README.md"

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
            Settings.windowWidth.set(w)
            Settings.windowHeight.set(h)
            config.saveConfig()

    def loadFile(self, filename):
        self.removeGraphicOptions()
        if os.path.exists(filename):
            try:
                self.editor.loadFile(filename)
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

    closeMinecraftWarning = Settings.closeMinecraftWarning.configProperty()

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
        if 0 == len(alphaMaterials.yamlDatas):
            albow.alert("Failed to load minecraft.yaml. Check the console window for details.")

        if mcedit.closeMinecraftWarning:
            answer = albow.ask("Warning: You must close Minecraft completely before editing. Save corruption may result", ["Don't remind me again.", "OK"], default=1, cancel=1)
            if answer == "Don't remind me again.":
                mcedit.closeMinecraftWarning = False

        config.saveConfig()

        while True:
            try:
                root_widget.run()
            except SystemExit:
                config.saveConfig()
                mcedit.editor.renderer.discardAllChunks()
                mcedit.editor.deleteAllCopiedSchematics()
                raise
            except MemoryError:
                traceback.print_exc()
                mcedit.editor.handleMemoryError()


def main(argv):
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
        w, h = (Settings.windowWidth.get(), Settings.windowHeight.get())
        return max(20, w), max(20, h)

    def displayMode(self):
        displayMode = pygame.OPENGL | pygame.RESIZABLE
        if Settings.doubleBuffer.get():
            displayMode |= pygame.DOUBLEBUF
        return displayMode

    def reset(self):
        pygame.key.set_repeat(500, 100)

        try:
            display.gl_set_attribute(pygame.GL_SWAP_CONTROL, Settings.vsync.get())
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
        return self.terrainTextures.get(level.materials.name, self.terrainTextures["Alpha"])

    def loadTextures(self):
        self.terrainTextures = {}

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

        # TODO probably simplify this
        textures = (
            (pymclevel.materials.alphaMaterials, 'terrain.png'),
        )

        for mats, matFile in textures:
            try:
                if mats.name == 'Alpha':
                    tex = mceutils.loadTerrainTexture()
                else:
                    tex = mceutils.loadPNGTexture(matFile)
                self.terrainTextures[mats.name] = tex
            except Exception as e:
                logging.warning(
                    'Unable to load terrain from {0}, using flat colors.'
                    'Error was: {1!r}'.format(matFile, e)
                )
                self.terrainTextures[mats.name] = glutils.Texture(
                    functools.partial(makeTerrainTexture, mats)
                )
            mats.terrainTexture = self.terrainTextures[mats.name]


mcplatform.os_ops.handle_init()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
