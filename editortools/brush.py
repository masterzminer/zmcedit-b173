from __future__ import annotations

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



from mceutils import ChoiceButton
from os.path import basename
import tempfile
from .toolbasics import *
from functools import reduce
import numpy as np
from pymclevel.material import materials, natural_block_mask
from config import LastDir, Keys, BrushToolSettings
import log
from bresenham import bresenham
from pathlib import Path

from pymclevel.box import BoundingBox
from pymclevel.schematic import MCSchematic

class BrushMode(object):
    def dirtyBoxForPointAndOptions(self, point):
        # also used to position the preview reticle
        size = _get_brush_size()
        origin = list(map(lambda x, s: x - (s >> 1), point, size))
        return BoundingBox(origin, size)

    def performAtPoint(self, op, point, dirtyBox):
        pass

    def createOptions(self, panel, tool):
        pass


def _get_brush_size():
    return (
        BrushToolSettings.length.v,
        BrushToolSettings.height.v,
        BrushToolSettings.width.v,
    )

class Modes:
    class Fill(BrushMode):
        name = "Fill"

        def createOptions(self, panel, tool):
            col = [
                panel.modeStyleGrid,
                panel.hollowRow,
                panel.noiseInput,
                panel.brushSizeRows,
                panel.blockButton,
            ]
            return col

        def performAtPoint(self, op: BrushOperation, point, dirtyBox):
            for chunk, slices, point in op.level.getChunkSlices(dirtyBox):
                worldPoint = [p + o for p, o in zip(point, dirtyBox.origin)]
                blocks = chunk.Blocks[slices]

                box = BoundingBox(worldPoint, (blocks.shape[0], blocks.shape[2], blocks.shape[1]))  # xzy reorder

                brushMask = op.createBrushMask(op.brushSize, BrushToolSettings.shape.v, dirtyBox.origin, box, op.noise, op.noise_type, op.hollow)
                blocks[brushMask] = op.blockInfo.ID

                chunk.Data[slices][brushMask] = op.blockInfo.blockData

    class FloodFill(BrushMode):
        name = "Flood Fill"

        def createOptions(self, panel, tool):
            col = [
                panel.brushModeRow,
                panel.blockButton
            ]
            indiscriminateButton = CheckBoxLabel("Indiscriminate", ref=BrushToolSettings.flood_indiscriminate)

            col.append(indiscriminateButton)
            return col

        def performAtPoint(self, op, point, dirtyBox):

            tmpfile = tempfile.mkdtemp("FloodFillUndo")
            undoLevel = MCBetaLevel(tmpfile, create=True)
            dirtyChunks = set()

            def saveUndoChunk(cx, cz):
                if (cx, cz) in dirtyChunks:
                    return
                dirtyChunks.add((cx, cz))
                b = BoundingBox((cx * 16, 0, cz * 16), (16, 128, 16))
                undoLevel.copyBlocksFrom(op.level, b, b.origin, create=True)

            doomedBlock = op.level.blockAt(*point)
            doomedBlockData = op.level.blockDataAt(*point)
            checkData = (doomedBlock not in (8, 9, 10, 11))
            indiscriminate = BrushToolSettings.flood_indiscriminate.v

            if doomedBlock == op.blockInfo.ID:
                return
            if indiscriminate:
                checkData = False
                if doomedBlock == 2:  # grass
                    doomedBlock = 3  # dirt

            x, y, z = point
            saveUndoChunk(x // 16, z // 16)
            op.level.setBlockAt(x, y, z, op.blockInfo.ID)
            op.level.setBlockDataAt(x, y, z, op.blockInfo.blockData)

            def processCoords(coords):
                new_coords = deque()

                for (x, y, z) in coords:
                    for _dir, offsets in faceDirections:
                        dx, dy, dz = offsets
                        p = (x + dx, y + dy, z + dz)

                        nx, ny, nz = p
                        b = op.level.blockAt(nx, ny, nz)
                        if indiscriminate:
                            if b == 2:
                                b = 3
                        if b == doomedBlock:
                            if checkData:
                                if op.level.blockDataAt(nx, ny, nz) != doomedBlockData:
                                    continue

                            saveUndoChunk(nx // 16, nz // 16)
                            op.level.setBlockAt(nx, ny, nz, op.blockInfo.ID)
                            op.level.setBlockDataAt(nx, ny, nz, op.blockInfo.blockData)
                            new_coords.append(p)

                return new_coords

            def spread(coords):
                while len(coords):
                    start = datetime.now()

                    num = len(coords)
                    coords = processCoords(coords)
                    d = datetime.now() - start
                    progress = "Did {0} coords in {1}".format(num, d)
                    log.debug(progress)
                    yield progress

            showProgress("Flood fill...", spread([point]), cancel=True)
            op.editor.invalidateChunks(dirtyChunks)
            op.undoSchematic = undoLevel

    class Replace(Fill):
        name = "Replace"

        def createOptions(self, panel, tool):
            return Modes.Fill.createOptions(self, panel, tool) + [panel.replaceBlockButton]

        def performAtPoint(self, op: BrushOperation, point, dirtyBox):
            for i, (chunk, slices, point) in enumerate(op.level.getChunkSlices(dirtyBox)):
                yield i, dirtyBox.chunkCount

                worldPoint = [p + o for p, o in zip(point, dirtyBox.origin)]
                blocks = chunk.Blocks[slices]
                data = chunk.Data[slices]
                box = BoundingBox(worldPoint, (blocks.shape[0], blocks.shape[2], blocks.shape[1]))  # xzy reorder

                brushMask = op.createBrushMask(op.brushSize, BrushToolSettings.shape.v, dirtyBox.origin, box, op.noise, op.noise_type, op.hollow)

                replaceWith = BrushToolSettings.replace_block.get()
                # xxx pasted from fill.py
                if op.blockInfo.wildcard:
                    log.trace("Wildcard replace")
                    blocksToReplace = []
                    for i in range(16):
                        blocksToReplace.append(materials.blockWithID(op.blockInfo.ID, i))
                else:
                    blocksToReplace = [op.blockInfo]

                replaceTable = op.level.blockReplaceTable(blocksToReplace)
                replaceMask = replaceTable[blocks, data]
                brushMask &= replaceMask

                blocks[brushMask] = replaceWith.ID
                data[brushMask] = replaceWith.blockData

    class Erode(BrushMode):
        name = "Erode"

        def createOptions(self, panel, tool):
            col = [
                panel.modeStyleGrid,
                panel.brushSizeRows,
            ]
            col.append(IntInputRow("Strength: ", ref=BrushToolSettings.erode_strength, min=1, max=20, tooltipText="Number of times to apply erosion. Larger numbers are slower."))
            return col

        def performAtPoint(self, op: BrushOperation, point, dirtyBox):
            box = dirtyBox.expand(1)

            strength = BrushToolSettings.erode_strength.v

            erosionArea = op.level.extractSchematic(box, entities=False)
            if erosionArea is None:
                return

            blocks = erosionArea.Blocks
            data = erosionArea.Data
            bins = np.bincount(blocks.ravel())
            fillBlockID = bins.argmax()

            def getNeighbors(solidBlocks):
                neighbors = np.zeros(solidBlocks.shape, dtype='uint8')
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[:-2, 1:-1, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[2:, 1:-1, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, :-2, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 2:, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 1:-1, :-2]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 1:-1, 2:]
                return neighbors

            for i in range(strength):
                solidBlocks = blocks != 0
                neighbors = getNeighbors(solidBlocks)

                brushMask = op.createBrushMask(op.brushSize, BrushToolSettings.shape.v)
                erodeBlocks = neighbors < 5
                erodeBlocks &= (np.random.random(erodeBlocks.shape) > 0.3)
                erodeBlocks[1:-1, 1:-1, 1:-1] &= brushMask
                blocks[erodeBlocks] = 0

                solidBlocks = blocks != 0
                neighbors = getNeighbors(solidBlocks)

                fillBlocks = neighbors > 2
                fillBlocks &= ~solidBlocks
                fillBlocks[1:-1, 1:-1, 1:-1] &= brushMask
                blocks[fillBlocks] = fillBlockID

            op.level.copyBlocksFrom(erosionArea, erosionArea.bounds.expand(-1), dirtyBox.origin)

    class Topsoil(Fill):
        name = "Topsoil"

        def createOptions(self, panel, tool):
            col = Modes.Fill.createOptions(self, panel, tool)
            depthRow = IntInputRow("Depth: ", ref=BrushToolSettings.topsoil_depth)
            naturalRow = CheckBoxLabel("Only Change Natural Earth", ref=BrushToolSettings.topsoil_natural_earth)
            col.extend([depthRow, naturalRow])
            return col

        def performAtPoint(self, op: BrushOperation, point, dirtyBox):

            for chunk, slices, point in op.level.getChunkSlices(dirtyBox):
                depth = BrushToolSettings.topsoil_depth.v
                blocks = chunk.Blocks[slices]
                data = chunk.Data[slices]

                worldPoint = [p + o for p, o in zip(point, dirtyBox.origin)]

                box = BoundingBox(worldPoint, (blocks.shape[0], blocks.shape[2], blocks.shape[1]))  # xzy reorder

                brushMask = op.createBrushMask(op.brushSize, BrushToolSettings.shape.v, dirtyBox.origin, box, op.noise, op.noise_type, op.hollow)

                blocktype = op.blockInfo

                if BrushToolSettings.topsoil_natural_earth.v:
                    block_mask = natural_block_mask()
                    block_mask[blocktype.ID] = True
                    blocktypeMask = block_mask[blocks]

                else:
                    # topsoil any block
                    blocktypeMask = blocks != 0

                if depth < 0:
                    blocktypeMask &= (blocks != blocktype.ID)

                heightmap = extractHeights(blocktypeMask)

                for x, z in np.ndindex(heightmap.shape):
                    h = heightmap[x, z]
                    if h >= box.height:
                        return
                    if depth > 0:
                        idx = x, z, slice(max(0, h - depth), h)
                    else:
                        # negative depth values mean to put a layer above the surface
                        idx = x, z, slice(h, min(blocks.shape[2], h - depth))
                    mask = brushMask[idx]
                    blocks[idx][mask] = blocktype.ID
                    data[idx][mask] = blocktype.blockData

    class Paste(BrushMode):

        name = "Paste"

        _level_offset = [0, 0, 0]
        _paste_level = MCSchematic(shape=(1, 1, 1))
        _loaded_schematic_name = None

        def _get_paste_offset(self):
            return (
                BrushToolSettings.copy_offset_x.v,
                BrushToolSettings.copy_offset_y.v,
                BrushToolSettings.copy_offset_z.v,
            )

        def _update_paste_offset(self, index, value):
            if index == 0: BrushToolSettings.copy_offset_x.set(value)
            elif index == 1: BrushToolSettings.copy_offset_y.set(value)
            elif index == 2: BrushToolSettings.copy_offset_z.set(value)

        def _reset_paste_offset(self):
            BrushToolSettings.copy_offset_x.set(0)
            BrushToolSettings.copy_offset_y.set(0)
            BrushToolSettings.copy_offset_z.set(0)

        def find_centered_point(self, point):
            return [p + c + lev for p, c, lev in zip(point, self._get_paste_offset(), self._level_offset)]
        
        def dirtyBoxForPointAndOptions(self, point):
            p = self._paste_level
            return BoundingBox(self.find_centered_point(point), [p.Width, p.Height, p.Length])

        
        def importPaste(self, tool):
            filename = mcplatform.askOpenFile(LastDir.schematic, title='Choose a schematic...')
            # No file selected, do nothing
            if filename is None or filename == "":
                return False

            return self.load_paste(tool, filename)

        def load_paste(self, tool, clipFilename):
            if clipFilename:
                try:
                    self._loaded_schematic_name = None
                    self._load_level(tool, fromFile(clipFilename))
                except Exception:
                    alert(f"Failed to load file {clipFilename}")
                    # On failure, load an empty schematic
                    self._load_level(tool, MCSchematic(shape=(1, 1, 1)))
                    return False

            BrushToolSettings.copy_schematic.set(clipFilename)
            return True

        def createOptions(self, panel, tool):
            col = [panel.brushModeRow]

            importButton = Button("Import", action=lambda: self.importPaste(tool))
            self.clearButton = Button("Clear", action=lambda: BrushToolSettings.copy_schematic.set(""))
            self.importRow = Row((importButton, self.clearButton))
                
            BrushToolSettings.copy_schematic.add_observer(lambda v: self.update_copy_schematic(v, tool), "paste mode")

            self._update_paste(tool)

            tool.centerx, tool.centery , tool.centerz = self._round_level(tool.level)
            class CenterRef:
                def __init__(c_self, i):
                    c_self.i = i
                def get(c_self):
                    return self._get_paste_offset()[c_self.i]
                def set(c_self, v):
                    self._update_paste_offset(c_self.i, v)
            
            cx, cy, cz = [IntInputRow(c, width=40, ref=CenterRef(i)) for i, c in zip((0, 1, 2), "xyz")]

            centerRow = Row((cx, cy, cz))

            importLabel = ValueDisplay(width=150, ref=BrushToolSettings.copy_schematic, format_func=lambda v: ("Loaded: " + Path(v).stem) if v != "" else "")


            create_chunks_box = self._checkbox("Create Chunks", BrushToolSettings.copy_create_chunks, "When brushing into missing chunks, create new empty chunks")
            copy_air_check_box = self._checkbox("Copy Air", BrushToolSettings.copy_paste_air, "Paste air blocks from the brush")
            copy_water_check_box = self._checkbox("Copy Water", BrushToolSettings.copy_paste_water, "Paste water and lava blocks from the brush")

            reset_button = Button("Reset", action=self._reset_paste_offset)
            
            copy_chunks_row = Row((reset_button, create_chunks_box))

            col.extend([self.importRow, importLabel, centerRow, copy_chunks_row, copy_air_check_box, copy_water_check_box])

            self.update_copy_schematic(BrushToolSettings.copy_schematic.v, tool)

            return col

        def _checkbox(self, title, ref, tooltip):
            box = CheckBox(ref=ref)
            lab = Label(title)
            lab.mouse_down = box.mouse_down
            lab.tooltipText = box.tooltipText = tooltip
            return Row((box, lab))

        def post_panel_init(self, tool):
            self.update_copy_schematic(BrushToolSettings.copy_schematic.v, tool)

        def update_copy_schematic(self, v, tool):
            # Keep the setting updated
            if v != BrushToolSettings.copy_schematic.v:
                BrushToolSettings.copy_schematic.set(v)

            # No more schematic, remove the clear button
            if v == "":
                # Remove the button
                self.importRow.remove(self.clearButton)
                # Update the tool's loaded level
                # There's something to copy, copy it
                stack = tool.editor.copyStack
                if len(stack) > 0:
                    self._load_level(tool, stack[0])
                # Otherwise load an empty level
                else:
                    self._load_level(tool, MCSchematic(shape=(1, 1, 1)))

            # There is a schematic, add the clear button
            else:
                self.importRow.add(self.clearButton)


        def _update_paste(self, tool):
            # If a schematic was saved, use it
            imported = False
            saved_schematic = BrushToolSettings.copy_schematic.v
            if saved_schematic != "":
                # If the schematic to load is already available, load the already loaded level
                if self._loaded_schematic_name == saved_schematic and self._paste_level is not None:
                    self._load_level(tool, self._paste_level)
                    imported = True

                # Otherwise try to load it
                else:
                    loaded = self.load_paste(tool, saved_schematic)
                    # If it failed, reset the setting
                    if not loaded:
                        BrushToolSettings.copy_schematic.set("")
                    imported = loaded

            # If nothing was imported
            if not imported:
                # Found something to copy from, use it
                stack = tool.editor.copyStack
                if len(stack) > 0:
                    self._load_level(tool, stack[0])
                    imported = True

            # If still nothing was imported, init with an empty level
            if not imported:
                self._load_level(tool, MCSchematic(shape=(1, 1, 1)))



        def _round_brush(self, n):
            return 0 if n < 2 else n // 2

        def _round_level(self, level):
            return [
                -self._round_brush(level.Width),
                -self._round_brush(level.Height),
                -self._round_brush(level.Length),
            ]
            
        # Keep track of the level when it changes
        def _load_level(self, tool, level):
            old_level = self._paste_level

            self._paste_level = level
            tool.loadLevel(level)

            # Load a default offset to be near the middle of the level
            loaded = self._round_level(level)
            Width, Height, Length = loaded
            self._level_offset = [Width, Height, Length]

            if BrushToolSettings.copy_reset_on_select.v:
                reset = True
                if old_level == level:
                    reset = False
                elif hasattr(level, "filename") and hasattr(old_level, "filename"):
                    if level.filename is not None and old_level.filename is not None:
                        if level.filename != old_level.filename:
                            reset = False

                if reset:
                    self._reset_paste_offset()

            
            if hasattr(self._paste_level, "filename"):
                self._loaded_schematic_name = self._paste_level.filename
        

        def performAtPoint(self, op, point, dirtyBox):
            level = self._paste_level;
            point = self.find_centered_point(point)

            blocksToCopy = None
            if not (BrushToolSettings.copy_paste_air.v and BrushToolSettings.copy_paste_water.v):
                blocksToCopy = list(range(256))
                if not BrushToolSettings.copy_paste_air.v:
                    blocksToCopy.remove(0)
                if not BrushToolSettings.copy_paste_water.v:
                    blocksToCopy.remove(8)
                    blocksToCopy.remove(9)

            return op.level.copyBlocksFromIter(level, level.bounds, point, blocksToCopy=blocksToCopy, create=BrushToolSettings.copy_create_chunks.v)


brush_mode_classes = [
    Modes.Fill,
    Modes.FloodFill,
    Modes.Replace,
    Modes.Erode,
    Modes.Topsoil,
    Modes.Paste
]

brush_mode_map = {v.name: v() for v in brush_mode_classes}
brush_mode_name_list = [v.name for v in brush_mode_classes]

def get_brush_mode():
    return brush_mode_map[BrushToolSettings.mode.v]


brush_shapes = ["Round", "Square", "Diamond", "Pyramid"]

class BrushOperation(Operation):

    def __init__(self, editor, points):
        self.editor = editor
        self.level = editor.level
        if isinstance(points[0], (int, float)):
            points = [points]

        self.points = points

        self.brushSize = _get_brush_size()
        self.blockInfo = BrushToolSettings.fill_block.get()

        if max(self.brushSize) > BrushTool.maxBrushSize:
            self.brushSize = (BrushTool.maxBrushSize,) * 3
        if max(self.brushSize) < 1:
            self.brushSize = (1, 1, 1)

        boxes = [get_brush_mode().dirtyBoxForPointAndOptions(p) for p in points]
        self._dirtyBox = reduce(lambda a, b: a.union(b), boxes)

    undoSchematic = None


    @property
    def noise(self):
        return BrushToolSettings.chance.v
    
    @property
    def noise_type(self):
        return BrushToolSettings.chance_type.v

    @property
    def hollow(self):
        return BrushToolSettings.hollow.v

    @classmethod
    def createBrushMask(cls, shape, style="Round", offset=(0, 0, 0), box=None, chance=100, chance_type="edge", hollow=False):
        """
        Return a boolean array for a brush with the given shape and style.
        If 'offset' and 'box' are given, then the brush is offset into the world
        and only the part of the world contained in box is returned as an array
        """

        # we are returning indices for a Blocks array, so swap axes
        if box is None:
            box = BoundingBox(offset, shape)
        if chance < 100 or hollow:
            box = box.expand(1)

        outputShape = box.size
        outputShape = (outputShape[0], outputShape[2], outputShape[1])

        shape = shape[0], shape[2], shape[1]
        offset = array(offset) - array(box.origin)
        offset = offset[[0, 2, 1]]

        indices = np.indices(outputShape, dtype=float)
        half_shape = array([(i >> 1) - ((i & 1 == 0) and 0.5 or 0) for i in shape])

        blockCenters = indices - half_shape[:, np.newaxis, np.newaxis, np.newaxis]
        blockCenters -= offset[:, np.newaxis, np.newaxis, np.newaxis]

        shape = array(shape, dtype='float32')

        # Shapes that are then stretched based on the brush size

        # Sphere
        if style == "Round":
            blockCenters *= blockCenters
            shape /= 2
            shape *= shape

            blockCenters /= shape[:, np.newaxis, np.newaxis, np.newaxis]
            distances = sum(blockCenters, 0)
            mask = distances < 1

        # Rectangular prism
        elif style == "Square":
            blockCenters /= shape[:, np.newaxis, np.newaxis, np.newaxis]

            distances = np.absolute(blockCenters).max(0)
            mask = distances < .5

        # Diamond shape of square xz layers rotated 45 degrees
        elif style == "Diamond":
            blockCenters = np.abs(blockCenters)
            shape /= 2
            blockCenters /= shape[:, np.newaxis, np.newaxis, np.newaxis]
            distances = sum(blockCenters, 0)
            mask = distances < 1

        # Diamond shape of square xz layers aligned to the axes
        elif style == "Pyramid":
            blockCenters = np.abs(blockCenters)
            shape /= 2
            blockCenters /= shape[:, np.newaxis, np.newaxis, np.newaxis]

            y = blockCenters[2]
            xz = np.maximum(blockCenters[0], blockCenters[1])
            mask = xz + np.abs(y) < 1


        if (chance < 100 or hollow) and max(shape) > 1:
            threshold = chance / 100.0

            exposedBlockMask = None
            def compute_exposed():
                exposedBlockMask = np.ones(shape=outputShape, dtype='bool')
                exposedBlockMask[:] = mask
                sub_mask = mask[1:-1, 1:-1, 1:-1]
                exposedBlockSubMask = exposedBlockMask[1:-1, 1:-1, 1:-1]
                exposedBlockSubMask[:] = False

                # Finds blocks on the outside of the brush
                for dim in (0, 1, 2):
                    slices = [slice(1, -1), slice(1, -1), slice(1, -1)]
                    slices[dim] = slice(None, -2)
                    exposedBlockSubMask |= (sub_mask & (mask[tuple(slices)] != sub_mask))
                    slices[dim] = slice(2, None)
                    exposedBlockSubMask |= (sub_mask & (mask[tuple(slices)] != sub_mask))

                return exposedBlockMask

            # For hollow, all except those blocks will be excluded
            if hollow:
                exposedBlockMask = compute_exposed()
                mask[~exposedBlockMask] = False

            if chance < 100:
                # All outside blocks will have a chance of being excluded
                if chance_type == "edge":
                    if exposedBlockMask is None:
                        exposedBlockMask = compute_exposed()

                    r_mask = np.random.random(mask.shape) < threshold
                    mask[exposedBlockMask] = r_mask[exposedBlockMask]

                # All blocks have the same chance of being filled in
                elif chance_type == "full":
                    r_mask = np.random.random(mask.shape) < threshold
                    fullBlockMask = np.ones(shape=outputShape, dtype='bool')
                    fullBlockMask[:] = mask
                    mask[fullBlockMask] = r_mask[fullBlockMask]


        if chance < 100 or hollow:
            return mask[1:-1, 1:-1, 1:-1]
        else:
            return mask

    def dirtyBox(self):
        return self._dirtyBox

    def undo(self):
        if self.undoSchematic:
            self.level.removeEntitiesInBox(self._dirtyBox)
            self.level.removeTileEntitiesInBox(self._dirtyBox)

            if get_brush_mode().name == "Flood Fill":
                i = self.level.copyBlocksFromIter(self.undoSchematic,
                                          self.undoSchematic.bounds,
                                          self.undoSchematic.bounds.origin
                                          )

            else:
                i = self.level.copyBlocksFromIter(self.undoSchematic,
                                          BoundingBox((0, 0, 0), self._dirtyBox.size),
                                          self._dirtyBox.origin
                                          )

            showProgress("Undoing brush...", i)
            self.editor.invalidateChunks(self.undoSchematic.allChunks)

    def perform(self, recordUndo=True):
        if recordUndo:
            self.undoSchematic = self.extractUndoSchematicFrom(self.level, self._dirtyBox)

        def _perform():
            for i, point in enumerate(self.points):
                yield i, len(self.points), f"Applying {get_brush_mode().name} brush..."
                f = self.performAtPoint(point)
                if hasattr(f, "__iter__"):
                    for i in f:
                        yield i

        if len(self.points) > 10:
            showProgress("Performing brush...", _perform(), cancel=True)
        else:
            exhaust(_perform())

        for cPos in self._dirtyBox.chunkPositions:
            if self.level.containsChunk(*cPos):
                ch = self.level.getChunk(*cPos)
                ch.chunkChanged()

    def performAtPoint(self, point):
        dirtyBox = get_brush_mode().dirtyBoxForPointAndOptions(point)
        return get_brush_mode().performAtPoint(self, point, dirtyBox)


class BrushPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        self.brushModeButton = ChoiceButton([m for m in brush_mode_name_list],
                                            width=150,
                                            default_choice=BrushToolSettings.mode.v,
                                            choose=lambda: BrushToolSettings.mode.set(self.brushModeButton.selectedChoice))

        self.brushModeRow = Row((Label("Mode:"), self.brushModeButton))

        self.brushShapeButton = ChoiceButton(brush_shapes,
                                            width=self.brushModeButton.width,
                                            default_choice=BrushToolSettings.shape.v,
                                            choose=lambda: BrushToolSettings.shape.set(self.brushShapeButton.selectedChoice))

        self.brushShapeButton.tooltipText = f"Shortcut: ALT-{Keys.tool_option_1}"

        self.brushStyleRow = Row((Label("Brush:"), self.brushShapeButton))

        self.modeStyleGrid = Column([
            self.brushModeRow,
            self.brushStyleRow,
        ])

        shapeRows = []

        for d in [
            (BrushToolSettings.length, "L"),
            (BrushToolSettings.width, "W"),
            (BrushToolSettings.height, "H")
        ]:
            l = Label(d[1])
            f = IntField(ref=d[0], min=1, max=tool.maxBrushSize)
            row = Row((l, f))
            shapeRows.append(row)

        self.brushSizeRows = Column(shapeRows)

        self.noiseInputValue = IntInputRow("Chance: ", ref=BrushToolSettings.chance, min=0, max=100)
        self.noiseTypeInput = ChoiceButton(
            ["edge", "full"], choice_display={"edge": "Edge", "full": "Full"}, 
            choose=lambda: BrushToolSettings.chance_type.set(self.noiseTypeInput.selectedChoice),
            default_choice=BrushToolSettings.chance_type.v
        )
        self.noiseInput = Row([self.noiseInputValue, self.noiseTypeInput])

        hollowCheckBox = CheckBox(ref=BrushToolSettings.hollow)
        hollowLabel = Label("Hollow")
        hollowLabel.mouse_down = hollowCheckBox.mouse_down
        hollowLabel.tooltipText = hollowCheckBox.tooltipText = f"Shortcut: ALT-{Keys.tool_option_3}"

        self.hollowRow = Row((hollowCheckBox, hollowLabel))

        self.blockButton = BlockButton(
            blockInfo=BrushToolSettings.fill_block.v,
            on_block_info_change=BrushToolSettings.fill_block.set,
            recentBlocks=BrushToolSettings.fill_recent.v,
            on_recent_blocks_change=BrushToolSettings.fill_recent.set,
            allowWildcards=(get_brush_mode().name == "Replace"))

        self.replaceBlockButton = BlockButton(
            blockInfo=BrushToolSettings.replace_block.v,
            on_block_info_change=BrushToolSettings.replace_block.set,
            recentBlocks=BrushToolSettings.replace_recent.v,
            on_recent_blocks_change=BrushToolSettings.replace_recent.set)

        # Always update the block buttons when the settings change
        BrushToolSettings.fill_block.add_observer(lambda v: self.blockButton.update_block_info(v, False), "brush panel")
        BrushToolSettings.replace_block.add_observer(lambda v: self.replaceBlockButton.update_block_info(v, False), "brush panel")

        brush_mode = get_brush_mode()
        col = brush_mode.createOptions(self, tool)

        if brush_mode.name != "Flood Fill":
            spaceRow = IntInputRow("Line Spacing", ref=BrushToolSettings.minimum_spacing, min=1, tooltipText="Minimum number of blocks between brush strokes. Hold SHIFT to draw lines")
            col.append(spaceRow)
        col = Column(col)

        self.add(col)

        self.post_panel_init(tool)

        self.shrink_wrap()


    def post_panel_init(self, tool):
        pass

    def pickFillBlock(self):
        self.blockButton.action()
        self.tool.setupPreview()

    def pickReplaceBlock(self):
        self.replaceBlockButton.action()
        self.tool.setupPreview()

    def swap(self):
        b = self.blockButton.blockInfo
        self.blockButton.update_block_info(self.replaceBlockButton.blockInfo, False)
        self.replaceBlockButton.update_block_info(b, False)

        t = [b for b in self.blockButton._recentBlocks]
        self.blockButton.replace_recent_blocks([b for b in self.replaceBlockButton._recentBlocks])
        self.replaceBlockButton.replace_recent_blocks(t)

class BrushToolOptions(ToolOptions):
    def __init__(self):
        Panel.__init__(self)
        alphaField = FloatField(ref=BrushToolSettings.alpha, min=0.0, max=1.0, width=60)
        alphaField.increment = 0.1
        alphaRow = Row((Label("Alpha: "), alphaField))
        autoChooseCheckBox = CheckBoxLabel("Choose Block Immediately", ref=BrushToolSettings.choose_block_immediately,
                                            tooltipText="When the brush tool is chosen, prompt for a block type.")

        updateOffsetCheckBox = CheckBoxLabel("Reset Distance When Brush Size Changes", ref=BrushToolSettings.update_offset,
                                            tooltipText="Whenever the brush size changes, reset the distance to the brush blocks.")
        
        auto_reset_on_select_check_box = CheckBoxLabel("Reset Schematic Position On Select", ref=BrushToolSettings.copy_reset_on_select,
                                            tooltipText="When selecting a new schematic for the paste brush, reset the offset to the center")

        col = Column((Label("Brush Options"), alphaRow, autoChooseCheckBox, updateOffsetCheckBox, auto_reset_on_select_check_box, Button("OK", action=self.dismiss)))
        self.add(col)
        self.shrink_wrap()
        return

from .clone import CloneTool


class BrushTool(CloneTool):
    tooltipText = "Brush\nRight-click for options"
    toolIconName = "brush"

    def __init__(self, *args):
        CloneTool.__init__(self, *args)
        self.optionsPanel = BrushToolOptions()
        self.draggedPositions = []

        BrushToolSettings.length.add_observer(self._setBrushSize, "brush tool")
        BrushToolSettings.width.add_observer(self._setBrushSize, "brush tool")
        BrushToolSettings.height.add_observer(self._setBrushSize, "brush tool")
        BrushToolSettings.alpha.add_observer(lambda v: self.setupPreview(), "brush tool")
        def mode_change(v):
            self.brush_mode_changed()
            self.setupPreview()
        BrushToolSettings.mode.add_observer(mode_change, "brush tool")
        BrushToolSettings.shape.add_observer(lambda v: self.setupPreview(), "brush tool preview")
        BrushToolSettings.shape.add_observer(lambda v: self.brush_mode_changed(), "brush tool mode")
        BrushToolSettings.fill_block.add_observer(lambda v: self.setupPreview(), "brush tool")
        BrushToolSettings.replace_block.add_observer(lambda v: self.setupPreview(), "brush tool")

    panel = None

    def _setBrushSize(self, brushSize):
        if BrushToolSettings.update_offset.v:
            self.reticleOffset = self.offsetMax()
            self.resetToolDistance()
        self.previewDirty = True

    previewDirty = False

    _reticleOffset = 1

    @property
    def reticleOffset(self):
        if get_brush_mode().name == "Flood Fill":
            return 0
        return self._reticleOffset

    @reticleOffset.setter
    def reticleOffset(self, val):
        self._reticleOffset = val

    @property
    def brushSize(self):
        if get_brush_mode().name == "Flood Fill":
            return 1, 1, 1
        return _get_brush_size()

    @brushSize.setter
    def brushSize(self, val):
        (w, h, l) = [max(1, min(i, self.maxBrushSize)) for i in val]
        BrushToolSettings.height.set(h)
        BrushToolSettings.length.set(l)
        BrushToolSettings.width.set(w)

    maxBrushSize = 4096


    def brush_mode_changed(self):
        self.hidePanel()
        self.showPanel()

    def loadLevel(self, level):
        self.level = level
        self.centerx, self.centery, self.centerz = -level.Width // 2, 0, -level.Length // 2
        CloneTool.setupPreview(self)

    @property
    def statusText(self):
        return (
            f"Click and drag to place blocks. ALT-Click to use the block under the cursor. "
            f"{Keys.roll.v.upper()} to increase and "
            f"{Keys.flip.v.upper()} to decrease size. "
            f"{Keys.rotate.v.upper()} to rotate, "
            f"{Keys.mirror.v.upper()} to roll. Mousewheel to adjust distance."
        )

    @property
    def worldTooltipText(self):
        if (key.get_mods() & KMOD_ALT) and get_brush_mode().name != "Paste":
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                block_data = self.editor.level.blockDataAt(*pos)
                return "Click to use {0} ({1}:{2})".format(materials.names[blockID][block_data], blockID, block_data)

            except Exception as e:
                return repr(e)

        if get_brush_mode().name == "Flood Fill":
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                block_data = self.editor.level.blockDataAt(*pos)
                return "Click to replace {0} ({1}:{2})".format(materials.names[blockID][block_data], blockID, block_data)

            except Exception as e:
                return repr(e)

    def swapBrushShape(self):
        index = brush_shapes.index(BrushToolSettings.shape.v) + 1
        index %= len(brush_shapes)
        BrushToolSettings.shape.set(brush_shapes[index])

    def swapBrushModes(self):
        # Go to the next brush in the list
        brush_mode = get_brush_mode()
        index = brush_mode_name_list.index(brush_mode.name) + 1
        index %= len(brush_mode_name_list)
        # Update the current mode
        BrushToolSettings.mode.set(brush_mode_name_list[index])


    draggedDirection = (0, 0, 0)
    centerx = centery = centerz = 0

    @alertException
    def mouseDown(self, evt, pos, direction):
        if (key.get_mods() & KMOD_ALT) and get_brush_mode().name != "Paste":
            id = self.editor.level.blockAt(*pos)
            data = self.editor.level.blockDataAt(*pos)
            b = materials.blockWithID(id, data)
            if get_brush_mode().name == "Replace":
                BrushToolSettings.replace_block.set_block(id, data)
                self.panel.replaceBlockButton.blockInfo = b
            else:
                self.panel.blockButton.blockInfo = b

            return

        self.draggedDirection = direction
        point = [p + d * self.reticleOffset for p, d in zip(pos, direction)]
        self.dragLineToPoint(point)

    @alertException
    def mouseDrag(self, evt, pos, _dir):
        direction = self.draggedDirection
        if get_brush_mode().name != "Flood Fill":
            if len(self.draggedPositions):
                self.lastPosition = lastPoint = self.draggedPositions[-1]

                # If the distance from this position to the previous position is larger than the minimum spacing, add it
                if any([abs(a - b) >= BrushToolSettings.minimum_spacing.v for a, b in zip(pos, lastPoint)]):
                    point = [p + d * self.reticleOffset for p, d in zip(pos, direction)]
                    self.dragLineToPoint(point)

    def dragLineToPoint(self, point):
        if get_brush_mode().name == "Flood Fill":
            self.draggedPositions = [point]
            return

        if key.get_mods() & KMOD_SHIFT and len(self.draggedPositions):
            points = bresenham(self.draggedPositions[-1], point)
            self.draggedPositions.extend(points[1:])
        else:
            self.draggedPositions.append(point)

    @alertException
    def mouseUp(self, evt, pos, direction):
        if 0 == len(self.draggedPositions):
            return

        if get_brush_mode().name == "Flood Fill":
            self.draggedPositions = self.draggedPositions[-1:]

        op = BrushOperation(self.editor, self.draggedPositions)
        self.performWithRetry(op)

        box = op.dirtyBox()
        self.editor.addOperation(op)
        self.editor.addUnsavedEdit()

        self.editor.invalidateBox(box)
        self.lastPosition = self.draggedPositions[-1]

        self.draggedPositions = []

    def toolEnabled(self):
        return True

    def rotate(self):
        if get_brush_mode().name == "Paste":
            CloneTool.rotate(self)
            return
        
        offs = self.reticleOffset
        dist = self.editor.cameraToolDistance
        W, H, L = self.brushSize
        self.brushSize = L, H, W
        self.reticleOffset = offs
        self.editor.cameraToolDistance = dist

    def mirror(self):
        if get_brush_mode().name == "Paste":
            CloneTool.mirror(self)
            return

        offs = self.reticleOffset
        dist = self.editor.cameraToolDistance
        W, H, L = self.brushSize
        self.brushSize = W, L, H
        self.reticleOffset = offs
        self.editor.cameraToolDistance = dist

    def toolReselected(self):
        if get_brush_mode().name == "Paste":
            brush_mode_map["Paste"].importPaste(self)
        elif get_brush_mode().name == "Replace":
            self.panel.pickReplaceBlock()
        else:
            self.panel.pickFillBlock()

    def flip(self):
        if get_brush_mode().name == "Paste":
            CloneTool.flip(self)
            return

        self.decreaseBrushSize()

    def roll(self):
        if get_brush_mode().name == "Paste":
            CloneTool.roll(self)
            return

        self.increaseBrushSize()

    def swap(self):
        if get_brush_mode().name == "Paste": return

        self.panel.swap()

    def decreaseBrushSize(self):
        if get_brush_mode().name == "Paste": return

        self.brushSize = [i - 1 for i in self.brushSize]

    def increaseBrushSize(self):
        if get_brush_mode().name == "Paste": return

        self.brushSize = [i + 1 for i in self.brushSize]

    @alertException
    def setupPreview(self):
        self.previewDirty = False
        brushSize = self.brushSize

        # No need to set anything else up for the paste brush
        if get_brush_mode().name == "Paste":
            return
        
        if get_brush_mode().name == "Replace":
            blockInfo = BrushToolSettings.replace_block.get()
        else:
            blockInfo = BrushToolSettings.fill_block.get()

        class FakeLevel(MCLevel):
            filename = None

            def __init__(self):
                self.chunkCache = {}

            Width, Height, Length = brushSize

            zero_light = np.zeros((16, 16, Height), dtype='uint8')
            zero_light[:] = 15

            def getChunk(self, cx, cz):
                if (cx, cz) in self.chunkCache:
                    return self.chunkCache[cx, cz]

                class FakeBrushChunk(pymclevel.level.FakeChunk):
                    def compress(self):
                        del self.world.chunkCache[self.chunkPosition]
                    Entities = []
                    TileEntities = []

                f = FakeBrushChunk()
                f.world = self
                f.chunkPosition = (cx, cz)

                mask = BrushOperation.createBrushMask(brushSize, BrushToolSettings.shape.v, (0, 0, 0), BoundingBox((cx << 4, 0, cz << 4), (16, self.Height, 16)))
                f.Blocks = np.zeros(mask.shape, dtype='uint8')
                f.Data = np.zeros(mask.shape, dtype='uint8')
                f.BlockLight = self.zero_light
                f.SkyLight = self.zero_light

                if blockInfo.ID:
                    f.Blocks[mask] = blockInfo.ID
                    f.Data[mask] = blockInfo.blockData

                else:
                    f.Blocks[mask] = 255
                self.chunkCache[cx, cz] = f
                return f

        self.level = FakeLevel()

        CloneTool.setupPreview(self, alpha=BrushToolSettings.alpha.v)

    def resetToolDistance(self):
        distance = max(self.editor.cameraToolDistance, 6 + max(self.brushSize) * 1.25)
        self.editor.cameraToolDistance = distance

    def toolSelected(self):

        if BrushToolSettings.mode.v == "Paste":
            if BrushToolSettings.choose_block_immediately.v:
                blockPicker = BlockPicker(
                    BrushToolSettings.fill_block.get(),
                    allowWildcards=get_brush_mode().name == "Replace")

                if blockPicker.present():
                    self.panel.blockButton.blockInfo = blockPicker.blockInfo

        if BrushToolSettings.update_offset.v:
            self.reticleOffset = self.offsetMax()
        self.resetToolDistance()
        self.setupPreview()
        self.showPanel()

    def showPanel(self):
        if self.panel:
            self.panel.parent.remove(self.panel)

        panel = BrushPanel(self)
        panel.centery = self.editor.centery
        panel.left = self.editor.left
        panel.anchor = "lwh"

        self.panel = panel
        self.editor.add(panel)

    def increaseToolReach(self):
        if self.editor.mainViewport.mouseMovesCamera and not Settings.long_distance_mode.v:
            return False
        self.reticleOffset = self.reticleOffset + 1
        return True

    def decreaseToolReach(self):
        if self.editor.mainViewport.mouseMovesCamera and not Settings.long_distance_mode.v:
            return False
        self.reticleOffset = max(self.reticleOffset - 1, 0)
        return True

    def resetToolReach(self):
        if self.editor.mainViewport.mouseMovesCamera and not Settings.long_distance_mode.v:
            self.resetToolDistance()
        else:
            self.reticleOffset = self.offsetMax()
        return True

    cameraDistance = EditorTool.cameraDistance

    def offsetMax(self):
        return max(1, ((0.5 * max(self.brushSize)) + 1))

    def getReticleOffset(self):
        return self.reticleOffset

    def getReticlePoint(self, pos, direction):
        if len(self.draggedPositions):
            direction = self.draggedDirection
        return list(map(lambda a, b: a + (b * self.getReticleOffset()), pos, direction))

    def drawToolReticle(self):
        for pos in self.draggedPositions:
            drawTerrainCuttingWire(BoundingBox(pos, (1, 1, 1)),
                                   (0.75, 0.75, 0.1, 0.4),
                                   (1.0, 1.0, 0.5, 1.0))

    lastPosition = None

    def drawTerrainReticle(self):
        if (key.get_mods() & KMOD_ALT) and get_brush_mode().name != "Paste":
            # eyedropper mode
            self.editor.drawWireCubeReticle(color=(0.2, 0.6, 0.9, 1.0))
        else:
            pos, direction = self.editor.blockFaceUnderCursor
            reticlePoint = self.getReticlePoint(pos, direction)

            self.editor.drawWireCubeReticle(position=reticlePoint)
            if reticlePoint != pos:
                glColor4f(1.0, 1.0, 0.0, 0.7)
                with gl.glBegin(GL_LINES):
                    glVertex3f(*[a + 0.5 for a in reticlePoint])  # center of reticle block
                    glVertex3f(*list(map(lambda a, b: a + 0.5 + b * 0.5, pos, direction)))  # top side of surface block

            if self.previewDirty:
                self.setupPreview()

            brush_mode = get_brush_mode()
            dirtyBox = brush_mode.dirtyBoxForPointAndOptions(reticlePoint)
            self.drawTerrainPreview(dirtyBox.origin)
            if key.get_mods() & KMOD_SHIFT and self.lastPosition and brush_mode.name != "Flood Fill":
                glColor4f(1.0, 1.0, 1.0, 0.7)
                with gl.glBegin(GL_LINES):
                    glVertex3f(*[a + 0.5 for a in self.lastPosition])
                    glVertex3f(*[a + 0.5 for a in reticlePoint])

    def updateOffsets(self):
        pass

    def selectionChanged(self):
        pass

    def option1(self):
        self.swapBrushShape()

    def option2(self):
        self.swapBrushModes()

    def option3(self):
        BrushToolSettings.hollow.invert()
