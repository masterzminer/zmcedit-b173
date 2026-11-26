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



from .toolbasics import *

from pymclevel.box import BoundingBox
from pymclevel.material import materials
from config import Keys, FillToolSettings
import log

class BlockFillOperation(Operation):
    def __init__(self, editor, destLevel, destBox, blockInfo, blocksToReplace):
        self.editor = editor
        self.destLevel = destLevel
        self.destBox = destBox
        self.blockInfo = blockInfo
        self.blocksToReplace = blocksToReplace

    def name(self):
        return "Fill with " + self.blockInfo.name

    def perform(self, recordUndo=True):
        if recordUndo:
            self.undoSchematic = self.extractUndoSchematicFrom(self.destLevel, self.destBox)

        destBox = self.destBox
        if self.destLevel.bounds == self.destBox:
            destBox = None

        fill = self.destLevel.fillBlocksIter(destBox, self.blockInfo, blocksToReplace=self.blocksToReplace)
        showProgress("Replacing blocks...", fill, cancel=True)

    def undo(self):
        if self.undoSchematic:
            self.destLevel.removeEntitiesInBox(self.destBox)
            self.destLevel.removeTileEntitiesInBox(self.destBox)
            with setWindowCaption("Undoing - "):
                i = self.destLevel.copyBlocksFromIter(self.undoSchematic, BoundingBox((0, 0, 0), self.destBox.size), self.destBox.origin)
                showProgress("Copying {0:n} blocks...".format(self.destBox.volume), i)

    def bufferSize(self):
        return self.destBox.volume * 2

    def dirtyBox(self):
        return self.destBox


class FillToolPanel(Panel):

    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        self.blockButton = BlockButton(
            blockInfo=FillToolSettings.fill_block.v,
            on_block_info_change=FillToolSettings.fill_block.set,
            recentBlocks=FillToolSettings.fill_recent.v,
            on_recent_blocks_change=FillToolSettings.fill_recent.set)
        FillToolSettings.fill_block.add_observer(lambda v: self.blockButton.update_block_info(v, False), "fill panel")

        self.fillWithLabel = Label("Fill with:", width=self.blockButton.width, align="c")
        self.fillButton = Button("Fill", action=tool.confirm, width=self.blockButton.width)
        self.fillButton.tooltipText = f"Shortcut: {Keys.confirm_construction.v.upper()}"

        self.replaceLabel = replaceLabel = Label("Replace", width=self.blockButton.width)
        replaceLabel.mouse_down = lambda a: self.tool.toggleReplacing()
        replaceLabel.fg_color = (177, 177, 255, 255)
        replaceLabel.tooltipText = f"Shortcut: {Keys.roll.v.upper()}"
        replaceLabel.align = "c"

        col = (self.fillWithLabel,
                self.blockButton,
                replaceLabel,
                self.fillButton)

        self.replaceBlockButton = BlockButton(
            blockInfo=FillToolSettings.replace_block.v,
            on_block_info_change=FillToolSettings.replace_block.set,
            recentBlocks=FillToolSettings.replace_recent.v,
            on_recent_blocks_change=FillToolSettings.replace_recent.set)
        FillToolSettings.replace_block.add_observer(lambda v: self.replaceBlockButton.update_block_info(v, False), "fill panel")
        
        if tool.is_replacing():
            self.fillWithLabel = Label("Find:", width=self.blockButton.width, align="c")

            self.replaceLabel.text = "Replace with:"

            self.swapButton = Button("Swap", action=self.swapBlockTypes, width=self.blockButton.width)
            self.swapButton.fg_color = (255, 255, 255, 255)
            self.swapButton.highlight_color = (60, 255, 60, 255)

            self.swapButton.tooltipText = f"Shortcut: {Keys.swap.v.upper()}"

            self.fillButton = Button("Replace", action=tool.confirm, width=self.blockButton.width)
            self.fillButton.tooltipText = f"Shortcut: {Keys.confirm_construction.v.upper()}"

            col = (self.fillWithLabel,
                    self.blockButton,
                    replaceLabel,
                    self.replaceBlockButton,
                    self.swapButton,
                    self.fillButton)

        col = Column(col)

        self.add(col)
        self.shrink_wrap()

    def swapBlockTypes(self):
        b = self.blockButton.blockInfo
        self.blockButton.update_block_info(self.replaceBlockButton.blockInfo, False)
        self.replaceBlockButton.update_block_info(b, False)

        t = [b for b in self.blockButton._recentBlocks]
        self.blockButton.replace_recent_blocks([b for b in self.replaceBlockButton._recentBlocks])
        self.replaceBlockButton.replace_recent_blocks(t)

class FillToolOptions(ToolOptions):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        self.autoChooseCheckBox = CheckBoxLabel("Choose Block Immediately",
                                                ref=FillToolSettings.chose_block_immediately,
                                                tooltipText="When the fill tool is chosen, prompt for a block type")
        
        self.choose_block_on_swap_check_box = CheckBoxLabel("Choose Block On Swap",
                                                ref=FillToolSettings.chose_block_on_swap,
                                                tooltipText="When the swapping from fill to replace mode, prompt for a block type")        
        
        self.select_tool_after_check_box = CheckBoxLabel("Deselect After Fill",
                                                ref=FillToolSettings.select_tool_after,
                                                tooltipText="After filling, remove the current selection and move to the select tool")

        col = Column((Label("Fill Options"), self.autoChooseCheckBox, self.choose_block_on_swap_check_box, self.select_tool_after_check_box, Button("OK", action=self.dismiss)))

        self.add(col)
        self.shrink_wrap()


class FillTool(EditorTool):
    toolIconName = "fill"
    _blockInfo = materials.Stone
    replaceBlockInfo = materials.Air
    tooltipText = "Fill and Replace\nRight-click for options"

    def __init__(self, *args, **kw):
        EditorTool.__init__(self, *args, **kw)
        self.optionsPanel = FillToolOptions(self)

    def all_tool_icons(self):
        return ["fill"]

    def levelChanged(self):
        self.initTextures()

    def showPanel(self):
        if self.panel:
            self.panel.parent.remove(self.panel)

        panel = FillToolPanel(self)
        panel.centery = self.editor.centery
        panel.left = self.editor.left
        panel.anchor = "lwh"

        self.panel = panel
        self.editor.add(panel)

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def toolSelected(self):
        box = self.selectionBox()
        if None is box:
            return

        self.showPanel()

        if FillToolSettings.chose_block_immediately.v:
            if self.panel.blockButton.action():
                self.showPanel()

            else:
                self.editor.toolbar.selectTool(0)

    def toolReselected(self):
        self.showPanel()
        self.panel.blockButton.action()

    def cancel(self):
        self.hidePanel()

    def is_replacing(self):
        return FillToolSettings.mode.v == "replace"

    @alertException
    def confirm(self):
        box = self.selectionBox()
        if None is box:
            return

        with setWindowCaption("REPLACING - "):
            self.editor.freezeStatus("Replacing %0.1f million blocks" % (float(box.volume) / 1048576.,))

            fill_info = FillToolSettings.fill_block.v
            if self.is_replacing():
                blocksToReplace = []
                if fill_info.wildcard:
                    log.trace("Wildcard replace")
                    for i in range(16):
                        blocksToReplace.append(materials.blockWithID(fill_info.ID, i))
                else:
                    blocksToReplace.append(fill_info)

                op = BlockFillOperation(self.editor, self.editor.level, self.selectionBox(), FillToolSettings.replace_block.v, blocksToReplace)

            else:
                blocksToReplace = []
                op = BlockFillOperation(self.editor, self.editor.level, self.selectionBox(), fill_info, blocksToReplace)

            self.performWithRetry(op)

        self.editor.addOperation(op)

        self.editor.addUnsavedEdit()
        self.editor.invalidateBox(box)

        if FillToolSettings.select_tool_after.v:
            self.editor.toolbar.selectTool(-1)

    def roll(self):
        self.toggleReplacing()

    def toggleReplacing(self):
        if self.is_replacing():
            FillToolSettings.mode.set("fill")
        else:
            FillToolSettings.mode.set("replace")

        self.hidePanel()
        self.showPanel()
        if self.is_replacing() and FillToolSettings.chose_block_on_swap.v:
            self.panel.pickReplaceBlock()

    @alertException
    def swap(self):
        if self.panel and self.is_replacing():
            self.panel.swapBlockTypes()

    def initTextures(self):

        terrainTexture = materials.terrainTexture

        blockTextures = materials.blockTextures[:, 0]

        if hasattr(self, 'blockTextures'):
            for tex in self.blockTextures.values():
                tex.delete()

        self.blockTextures = {}

        def blockTexFunc(type):
            def _func():
                s, t = blockTextures[type][0]
                if not hasattr(terrainTexture, "data"):
                    return
                w, h = terrainTexture.data.shape[:2]
                s = int(float(s) * w / 256.0)
                t = int(float(t) * h / 256.0)
                texData = array(terrainTexture.data[t:t + h // 16, s:s + w // 16])
                glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w // 16, h // 16, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, texData)
            return _func

        for type in range(256):
            self.blockTextures[type] = Texture(blockTexFunc(type))

    def drawToolReticle(self):
        if key.get_mods() & KMOD_ALT:
            # eyedropper mode
            self.editor.drawWireCubeReticle(color=(0.2, 0.6, 0.9, 1.0))

    def drawToolMarkers(self):
        if self.editor.currentTool != self:
            return

        if self.panel and self.is_replacing():
            blockInfo = FillToolSettings.replace_block.v
        else:
            blockInfo = FillToolSettings.fill_block.v

        color = 1.0, 1.0, 1.0, 0.35
        if blockInfo:
            tex = self.blockTextures[blockInfo.ID]
            glMatrixMode(GL_TEXTURE)
            glPushMatrix()
            glScale(16., 16., 16.)

        else:
            tex = None

        glPolygonOffset(DepthOffset.FillMarkers, DepthOffset.FillMarkers)
        self.editor.drawConstructionCube(self.selectionBox(),
                                         color,
                                         texture=tex)

        if blockInfo:
            glMatrixMode(GL_TEXTURE)
            glPopMatrix()

    @property
    def statusText(self):
        return f"Press {self.hotkey} to choose a block. Press {Keys.roll.v.upper()} to enter replace mode. Click Fill or press {Keys.confirm_construction.v.upper()} to confirm"

    @property
    def worldTooltipText(self):
        if key.get_mods() & KMOD_ALT:
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                block_data = self.editor.level.blockDataAt(*pos)
                return "Click to use {0} ({1}:{2})".format(materials.blockWithID(blockID, block_data).name, blockID, block_data)

            except Exception as e:
                return repr(e)

    def mouseUp(self, *args):
        return self.editor.selectionTool.mouseUp(*args)

    @alertException
    def mouseDown(self, evt, pos, dir):
        if key.get_mods() & KMOD_ALT:
            id = self.editor.level.blockAt(*pos)
            data = self.editor.level.blockDataAt(*pos)

            FillToolSettings.fill_block.set(materials.blockWithID(id, data))
        else:
            return self.editor.selectionTool.mouseDown(evt, pos, dir)
