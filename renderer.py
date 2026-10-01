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


"""
renderer.py

What is going on in this file?

Here is an attempt to show the relationships between classes and
their responsibilities

MCRenderer:
    has "position", "origin", optionally "viewFrustum"
    Loads chunks near position+origin, draws chunks offset by origin
    Calls visible on viewFrustum to exclude chunks


    (+) ChunkRenderer
        Has "chunkPosition", "invalidLayers", "lists"
        One per chunk and detail level.
        Creates display lists from BlockRenderers

        (*) BlockRenderer
            Has "vertexArrays"
            One per block type, plus one for low detail and one for Entity

"""



from collections import defaultdict, deque
from datetime import datetime, timedelta
from depths import DepthOffset
from glutils import gl, Texture
import logging
import numpy as np
from OpenGL import GL
import pymclevel
import sys
from functools import reduce
import traceback
from pymclevel.level import FakeChunk
from pymclevel.materials import MCMaterials
import pymclevel.faces as Faces

from pymclevel.box import BoundingBox

def chunkMarkers(chunkSet):
    """ Returns a mapping { size: [position, ...] } for different powers of 2
    as size.
    """

    sizedChunks = defaultdict(list)
    size = 1

    def all4(cx, cz):
        cx &= ~size
        cz &= ~size
        return [(cx, cz), (cx + size, cz), (cx + size, cz + size), (cx, cz + size)]

    # lastsize = 6
    size = 1
    while True:
        nextsize = size << 1
        chunkSet = set(chunkSet)
        while len(chunkSet):
            cx, cz = chunkSet.pop()
            chunkSet.add((cx, cz))
            o = all4(cx, cz)
            others = set(o).intersection(chunkSet)
            if len(others) == 4:
                sizedChunks[nextsize].append(o[0])
                for c in others:
                    chunkSet.discard(c)
            else:
                for c in others:
                    sizedChunks[size].append(c)
                    chunkSet.discard(c)

        if len(sizedChunks[nextsize]):
            chunkSet = set(sizedChunks[nextsize])
            sizedChunks[nextsize] = []
            size <<= 1
        else:
            break
    return sizedChunks


class ChunkRenderer(object):
    maxlod = 2
    minlod = 0

    def __init__(self, renderer: MCRenderer, chunkPosition):
        self.renderer: MCRenderer = renderer
        self.blockRenderers = []
        self.detailLevel = 0
        self.invalidLayers = set(Layer.AllLayers)

        self.chunkPosition = chunkPosition
        self.bufferSize = 0
        self.renderstateLists = None

    @property
    def visibleLayers(self):
        return self.renderer.visibleLayers

    def forgetDisplayLists(self, states=None):
        if self.renderstateLists is not None:
            # print "Discarded {0}, gained {1} bytes".format(self.chunkPosition,self.bufferSize)

            for k in states or self.renderstateLists.keys():
                a = self.renderstateLists.get(k, [])
                # print a
                for i in a:
                    gl.glDeleteLists(i, 1)

            if states:
                del self.renderstateLists[states]
            else:
                self.renderstateLists = None

            self.needsRedisplay = True
            self.renderer.discardMasterList()

    def debugDraw(self):
        for blockRenderer in self.blockRenderers:
            blockRenderer.drawArrays(self.chunkPosition, False)

    def makeDisplayLists(self):
        if not self.needsRedisplay:
            return
        self.forgetDisplayLists()
        if not self.blockRenderers:
            return

        lists = defaultdict(list)

        showRedraw = self.renderer.showRedraw

        if not (showRedraw and self.needsBlockRedraw):
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        renderers = self.blockRenderers

        for blockRenderer in renderers:
            if self.detailLevel not in blockRenderer.detailLevels:
                continue
            if blockRenderer.layer not in self.visibleLayers:
                continue

            l = blockRenderer.makeArrayList(self.chunkPosition, self.needsBlockRedraw and showRedraw)
            lists[blockRenderer.renderstate].append(l)

        if not (showRedraw and self.needsBlockRedraw):
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

        self.needsRedisplay = False
        self.renderstateLists = lists

    @property
    def needsBlockRedraw(self):
        return Layer.Blocks in self.invalidLayers

    def invalidate(self, layers=None):
        if layers is None:
            layers = Layer.AllLayers

        if layers:
            layers = set(layers)
            self.invalidLayers.update(layers)
            blockRenderers = [br for br in self.blockRenderers
                              if br.layer is Layer.Blocks
                              or br.layer not in layers]
            if len(blockRenderers) < len(self.blockRenderers):
                self.forgetDisplayLists()
            self.blockRenderers = blockRenderers

            if self.renderer.showRedraw and Layer.Blocks in layers:
                self.needsRedisplay = True

    def calcFaces(self):
        minlod = self.renderer.detailLevelForChunk(self.chunkPosition)

        minlod = min(minlod, self.maxlod)
        if self.detailLevel != minlod:
            self.forgetDisplayLists()
            self.detailLevel = minlod
            self.invalidLayers.add(Layer.Blocks)

            # discard the standard detail renderers
            if minlod > 0:
                blockRenderers = []
                for br in self.blockRenderers:
                    if br.detailLevels != (0,):
                        blockRenderers.append(br)

                self.blockRenderers = blockRenderers

        if self.renderer.chunkCalculator:
            for i in self.renderer.chunkCalculator.calcFacesForChunkRenderer(self):
                yield

        else:
            return

    def vertexArraysDone(self):
        bufferSize = 0
        for br in self.blockRenderers:
            bufferSize += br.bufferSize()
            if self.renderer.alpha != 0xff:
                br.setAlpha(self.renderer.alpha)
        self.bufferSize = bufferSize
        self.invalidLayers = set()
        self.needsRedisplay = True
        self.renderer.invalidateMasterList()

    needsRedisplay = False

    @property
    def done(self):
        return len(self.invalidLayers) == 0

_XYZ = np.s_[..., 0:3]
_ST = np.s_[..., 3:5]
_XYZST = np.s_[..., :5]
_RGBA = np.s_[..., 20:24]
_RGB = np.s_[..., 20:23]
_A = np.s_[..., 23]


def makeVertexTemplates(xmin=0, ymin=0, zmin=0, xmax=1, ymax=1, zmax=1):
        return np.array([

             # FaceXIncreasing:
                              [[xmax, ymin, zmax, (zmin * 16), 16 - (ymin * 16), 0x0b],
                               [xmax, ymin, zmin, (zmax * 16), 16 - (ymin * 16), 0x0b],
                               [xmax, ymax, zmin, (zmax * 16), 16 - (ymax * 16), 0x0b],
                               [xmax, ymax, zmax, (zmin * 16), 16 - (ymax * 16), 0x0b],
                               ],

             # FaceXDecreasing:
                              [[xmin, ymin, zmin, (zmin * 16), 16 - (ymin * 16), 0x0b],
                               [xmin, ymin, zmax, (zmax * 16), 16 - (ymin * 16), 0x0b],
                               [xmin, ymax, zmax, (zmax * 16), 16 - (ymax * 16), 0x0b],
                               [xmin, ymax, zmin, (zmin * 16), 16 - (ymax * 16), 0x0b]],


             # FaceYIncreasing:
                              [[xmin, ymax, zmin, xmin * 16, 16 - (zmax * 16), 0x11],  # ne
                               [xmin, ymax, zmax, xmin * 16, 16 - (zmin * 16), 0x11],  # nw
                               [xmax, ymax, zmax, xmax * 16, 16 - (zmin * 16), 0x11],  # sw
                               [xmax, ymax, zmin, xmax * 16, 16 - (zmax * 16), 0x11]],  # se

             # FaceYDecreasing:
                              [[xmin, ymin, zmin, xmin * 16, 16 - (zmax * 16), 0x08],
                               [xmax, ymin, zmin, xmax * 16, 16 - (zmax * 16), 0x08],
                               [xmax, ymin, zmax, xmax * 16, 16 - (zmin * 16), 0x08],
                               [xmin, ymin, zmax, xmin * 16, 16 - (zmin * 16), 0x08]],

             # FaceZIncreasing:
                              [[xmin, ymin, zmax, xmin * 16, 16 - (ymin * 16), 0x0d],
                               [xmax, ymin, zmax, xmax * 16, 16 - (ymin * 16), 0x0d],
                               [xmax, ymax, zmax, xmax * 16, 16 - (ymax * 16), 0x0d],
                               [xmin, ymax, zmax, xmin * 16, 16 - (ymax * 16), 0x0d]],

             # FaceZDecreasing:
                              [[xmax, ymin, zmin, xmin * 16, 16 - (ymin * 16), 0x0d],
                               [xmin, ymin, zmin, xmax * 16, 16 - (ymin * 16), 0x0d],
                               [xmin, ymax, zmin, xmax * 16, 16 - (ymax * 16), 0x0d],
                               [xmax, ymax, zmin, xmin * 16, 16 - (ymax * 16), 0x0d],
                              ],

        ])

elementByteLength = 24


def createPrecomputedVertices():
    height = 16
    precomputedVertices = [np.zeros(shape=(16, 16, height, 4, 6),  # x,y,z,s,t,rg, ba
                                  dtype='float32') for d in faceVertexTemplates]

    xArray = np.arange(16)[:, np.newaxis, np.newaxis, np.newaxis]
    zArray = np.arange(16)[np.newaxis, :, np.newaxis, np.newaxis]
    yArray = np.arange(height)[np.newaxis, np.newaxis, :, np.newaxis]

    for dir in range(len(faceVertexTemplates)):
        precomputedVertices[dir][_XYZ][..., 0] = xArray
        precomputedVertices[dir][_XYZ][..., 1] = yArray
        precomputedVertices[dir][_XYZ][..., 2] = zArray
        precomputedVertices[dir][_XYZ] += faceVertexTemplates[dir][..., 0:3]  # xyz

        precomputedVertices[dir][_ST] = faceVertexTemplates[dir][..., 3:5]  # s
        precomputedVertices[dir].view('uint8')[_RGB] = faceVertexTemplates[dir][..., 5, np.newaxis]
        precomputedVertices[dir].view('uint8')[_A] = 0xff

    return precomputedVertices

faceVertexTemplates = makeVertexTemplates()


class ChunkCalculator (object):
    cachedTemplate = None
    cachedTemplateHeight = 0

    whiteLight = np.array([[[15] * 16] * 16] * 16, np.uint8)
    precomputedVertices = createPrecomputedVertices()

    def __init__(self, level):
        self.makeRenderStates(level.materials)

        from leveleditor import Settings

        Settings.fastLeaves.addObserver(self)
        Settings.roughGraphics.addObserver(self)

        self.materialMap: np.ndarray
        """
        A 1D array of 256 ints defaulting to zero, seems to use block ids as an index to an int that represents the kind of block to render
        """

        self.blockRendererClasses: list
        """
        A list of all renderers for different kinds of blocks, the first element should be for rendering normal full blocks
        """

    class renderStatePlain(object):
        @classmethod
        def bind(self):
            pass

        @classmethod
        def release(self):
            pass

    class renderStateLowDetail(object):
        @classmethod
        def bind(self):
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_TEXTURE_2D)

        @classmethod
        def release(self):
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_TEXTURE_2D)

    class renderStateAlphaTest(object):
        @classmethod
        def bind(self):
            GL.glEnable(GL.GL_ALPHA_TEST)

        @classmethod
        def release(self):
            GL.glDisable(GL.GL_ALPHA_TEST)

    class _renderstateAlphaBlend(object):
        @classmethod
        def bind(self):
            GL.glEnable(GL.GL_BLEND)

        @classmethod
        def release(self):
            GL.glDisable(GL.GL_BLEND)

    class renderStateWater(_renderstateAlphaBlend):
        pass

    class renderStateIce(_renderstateAlphaBlend):
        pass

    class renderStateEntity(object):
        @classmethod
        def bind(self):
            GL.glDisable(GL.GL_DEPTH_TEST)
            # GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glEnable(GL.GL_BLEND)

        @classmethod
        def release(self):
            GL.glEnable(GL.GL_DEPTH_TEST)
            # GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glDisable(GL.GL_BLEND)

    renderStates = (
        renderStatePlain,
        renderStateLowDetail,
        renderStateAlphaTest,
        renderStateIce,
        renderStateWater,
        renderStateEntity,
    )

    def makeRenderStates(self, materials: MCMaterials):
        """
        materials: All data for every type of block
        """

        self.blockRendererClasses = [
            GenericBlockRenderer,
            LeafBlockRenderer,
            PlantBlockRenderer,
            TorchBlockRenderer,
            WaterBlockRenderer,
            SlabBlockRenderer,
        ]
        if materials.name in ("Alpha"):
            self.blockRendererClasses += [
                RailBlockRenderer,
                LadderBlockRenderer,
                SnowBlockRenderer,
                RedstoneBlockRenderer,
                IceBlockRenderer,
                FeatureBlockRenderer,
                StairBlockRenderer,
            # button, floor plate, door -> 1-cube features
            # lever, sign, wall sign, stairs -> 2-cube features

            # repeater
            # fence

            # bed
            # cake
            # portal
            ]

        # Init the materials to all zeros
        self.materialMap = materialMap = np.zeros((256,), np.uint8)
        # All materials after index 0 will be 1 by default. Value 0 is for air, value 1 is a normal block
        materialMap[1:] = 1

        # At this point, there are two materials, air and normal blocks
        currentMaterialMapId = 2

        # Go through all types of rendering, skipping the first element, which should be for rendering normal blocks
        for br in self.blockRendererClasses[1:]:
            # For all block ids that can be rendered by the current renderer br, set the material map render int to the current count, i.e. next renderer index
            materialMap[br.getBlocktypes(materials)] = currentMaterialMapId
            # Assign the current renderer index to the current renderer
            br.materialIndex = currentMaterialMapId
            # Move onto the next index
            currentMaterialMapId += 1

        # Copy the renderer indexes into another array for this class
        self.exposedMaterialMap = np.array(materialMap)
        # Give each transparent block type its own material id
        self.addTransparentMaterials(self.exposedMaterialMap, currentMaterialMapId)

    def addTransparentMaterials(self, mats, currentMaterialMapId):
        """
        mats: The array indexing block id to the index of the block renderer to use

        currentMaterialMapId: The next available material renderer id to assign
        """

        # Defining materials that should be considered transparent
        transparentMaterials = [
            pymclevel.materials.alphaMaterials.Glass,
            pymclevel.materials.alphaMaterials.MonsterSpawner,
            pymclevel.materials.alphaMaterials.Fire,
        ]
        # For each transparent material, give each one its own material renderer id
        for b in transparentMaterials:
            mats[b.ID] = currentMaterialMapId
            currentMaterialMapId += 1

    hiddenOreMaterials = np.arange(256, dtype='uint8')
    """A 1D array of each block id mapped to itself, and for specific blocks, they are instead set to 1 (stone)"""

    # don't show boundaries between dirt,grass,sand,gravel,stone
    hiddenOreMaterials[2] = 1
    hiddenOreMaterials[3] = 1
    hiddenOreMaterials[12] = 1
    hiddenOreMaterials[13] = 1

    roughMaterials = np.ones((256,), dtype='uint8')
    """A 1D array of each block id mapped to a 1, and for transparent blocks, incrementing values"""

    roughMaterials[0] = 0
    addTransparentMaterials(None, roughMaterials, 2)

    def calcFacesForChunkRenderer(self, cr: ChunkRenderer):
        if 0 == len(cr.invalidLayers):
#            layers = set(br.layer for br in cr.blockRenderers)
#            assert set() == cr.visibleLayers.difference(layers)

            return

        lod = cr.detailLevel
        cx, cz = cr.chunkPosition
        level = cr.renderer.level
        try:
            chunk = level.getChunk(cx, cz)
        except Exception as e:
            logging.warn(u"Error reading chunk: %s", e)
            yield
            return

        yield
        brs = []
        classes = [
            TileEntityRenderer,
            MonsterRenderer,
            ItemRenderer,
            TileTicksRenderer,
            TerrainPopulatedRenderer,
            LowDetailBlockRenderer,
            OverheadBlockRenderer,
        ]
        existingBlockRenderers = dict(((type(b), b) for b in cr.blockRenderers))

        for blockRendererClass in classes:
            if cr.detailLevel not in blockRendererClass.detailLevels:
                continue
            if blockRendererClass.layer not in cr.visibleLayers:
                continue
            if blockRendererClass.layer not in cr.invalidLayers:
                if blockRendererClass in existingBlockRenderers:
                    brs.append(existingBlockRenderers[blockRendererClass])

                continue

            br = blockRendererClass(self)
            br.detailLevel = cr.detailLevel

            for _ in br.makeChunkVertices(chunk):
                yield
            brs.append(br)

        blockRenderers = []

        # Recalculate high detail blocks if needed, otherwise retain the high detail renderers
        if lod == 0 and Layer.Blocks in cr.invalidLayers:
            for _ in self.calcHighDetailFaces(cr, blockRenderers):
                yield
        else:
            blockRenderers.extend(br for br in cr.blockRenderers if type(br) not in classes)

        # Add the layer renderers
        blockRenderers.extend(brs)
        cr.blockRenderers = blockRenderers

        cr.vertexArraysDone()
        return

    def getNeighboringChunks(self, chunk: FakeChunk):
        """
        chunk: The chunk to look for nearby chunks

        returns: A list of the 4 chunks next to the given chunk, these chunks may be fake empty chunks if none exists in that direction
        """
        
        cx, cz = chunk.chunkPosition
        level = chunk.world

        neighboringChunks = {}
        # Go through each of the 4 horizontal directions
        for dir, dx, dz in ((Faces.FaceXDecreasing, -1, 0),
                            (Faces.FaceXIncreasing, 1, 0),
                            (Faces.FaceZDecreasing, 0, -1),
                            (Faces.FaceZIncreasing, 0, 1)):
            # If the chunk next to the given chunk doesn't exist, then there will be an empty chunk "next" to it
            if not level.containsChunk(cx + dx, cz + dz):
                neighboringChunks[dir] = pymclevel.infiniteworld.ZeroChunk(level.Height)
            else:
                try:
                    # Set the chunk for that direction 
                    neighboringChunks[dir] = level.getChunk(cx + dx, cz + dz)
                except (pymclevel.mclevelbase.ChunkNotPresent, pymclevel.mclevelbase.ChunkMalformed):
                    # If there are any issues in getting the chunk, fall back to an empty chunk
                    neighboringChunks[dir] = pymclevel.infiniteworld.ZeroChunk(level.Height)
        return neighboringChunks

    def getAreaBlocks(self, chunk, neighboringChunks):
        """
        chunk: The chunk to get blocks near

        neighboringChunks: the chunks that are directly next to the given chunk in each of the 4 horizontal directions

        returns: A copy of the given chunk, with all axes expanded by one block containing the blocks of the chunks next to it on the 4 horizontal directions
        """

        # Create an initial array of all zeros, one block longer on every axis
        chunkWidth, chunkLength, chunkHeight = chunk.Blocks.shape
        areaBlocks = np.zeros((chunkWidth + 2, chunkLength + 2, chunkHeight + 2), np.uint8)

        # Copy the blocks of the given chunk into the areaBlocks, offset by one, leaving a one block edge around the chunk
        areaBlocks[1:-1, 1:-1, 1:-1] = chunk.Blocks
        # Copy the edge of each chunk next to the given chunk into the areaBlocks
        areaBlocks[:1, 1:-1, 1:-1] = neighboringChunks[pymclevel.faces.FaceXDecreasing].Blocks[-1:, :chunkLength, :chunkHeight]
        areaBlocks[-1:, 1:-1, 1:-1] = neighboringChunks[pymclevel.faces.FaceXIncreasing].Blocks[:1, :chunkLength, :chunkHeight]
        areaBlocks[1:-1, :1, 1:-1] = neighboringChunks[pymclevel.faces.FaceZDecreasing].Blocks[:chunkWidth, -1:, :chunkHeight]
        areaBlocks[1:-1, -1:, 1:-1] = neighboringChunks[pymclevel.faces.FaceZIncreasing].Blocks[:chunkWidth, :1, :chunkHeight]
        return areaBlocks

    def getFacingBlockIndices(self, areaBlockMats):
        """
        areaBlockMats: a 3D array of blocks, storing some id for rendering?

        returns: A list of each of the 6 faces, where each face is a slice of that faces block data from areaBlockMats
        """

        facingBlockIndices = [None] * 6

        exposedFacesX = (areaBlockMats[:-1, 1:-1, 1:-1] != areaBlockMats[1:, 1:-1, 1:-1])

        facingBlockIndices[pymclevel.faces.FaceXDecreasing] = exposedFacesX[:-1]
        facingBlockIndices[pymclevel.faces.FaceXIncreasing] = exposedFacesX[1:]

        exposedFacesZ = (areaBlockMats[1:-1, :-1, 1:-1] != areaBlockMats[1:-1, 1:, 1:-1])

        facingBlockIndices[pymclevel.faces.FaceZDecreasing] = exposedFacesZ[:, :-1]
        facingBlockIndices[pymclevel.faces.FaceZIncreasing] = exposedFacesZ[:, 1:]

        exposedFacesY = (areaBlockMats[1:-1, 1:-1, :-1] != areaBlockMats[1:-1, 1:-1, 1:])

        facingBlockIndices[pymclevel.faces.FaceYDecreasing] = exposedFacesY[:, :, :-1]
        facingBlockIndices[pymclevel.faces.FaceYIncreasing] = exposedFacesY[:, :, 1:]
        return facingBlockIndices

    def getAreaBlockLights(self, chunk, neighboringChunks):
        """
        chunk: The chunk to get lighting for

        neighboringChunks: The chunks directly next to the given chunk on the 4 horizontal directions

        returns: The expected light values for the chunk with one block expanded on every axis of the given chunk
        """

        chunkWidth, chunkLength, chunkHeight = chunk.Blocks.shape
        lights = chunk.BlockLight
        skyLight = chunk.SkyLight
        finalLight = self.whiteLight

        if lights is not None:
            finalLight = lights
        if skyLight is not None:
            finalLight = np.maximum(skyLight, lights)

        # Build out a chunk expanded by one block on all axes and default all light values to max
        areaBlockLights = np.ones((chunkWidth + 2, chunkLength + 2, chunkHeight + 2), np.uint8)
        areaBlockLights[:] = 15

        # Set all blocks of the original chunk to the computed light value
        areaBlockLights[1:-1, 1:-1, 1:-1] = finalLight

        # For each of the 4 directions at the edges of the chunk, use the maximum of either the computed skylight or block light at each of those positions
        nc = neighboringChunks[pymclevel.faces.FaceXDecreasing]
        np.maximum(nc.SkyLight[-1:, :chunkLength, :chunkHeight],
                nc.BlockLight[-1:, :chunkLength, :chunkHeight],
                areaBlockLights[0:1, 1:-1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceXIncreasing]
        np.maximum(nc.SkyLight[:1, :chunkLength, :chunkHeight],
                nc.BlockLight[:1, :chunkLength, :chunkHeight],
                areaBlockLights[-1:, 1:-1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceZDecreasing]
        np.maximum(nc.SkyLight[:chunkWidth, -1:, :chunkHeight],
                nc.BlockLight[:chunkWidth, -1:, :chunkHeight],
                areaBlockLights[1:-1, 0:1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceZIncreasing]
        np.maximum(nc.SkyLight[:chunkWidth, :1, :chunkHeight],
                nc.BlockLight[:chunkWidth, :1, :chunkHeight],
                areaBlockLights[1:-1, -1:, 1:-1])

        #  Force everything to be at least a light level of 4
        minimumLight = 4
        np.clip(areaBlockLights, minimumLight, 16, areaBlockLights)

        return areaBlockLights

    def calcHighDetailFaces(self, cr: ChunkRenderer, blockRenderers):
        """
        calculate the geometry for a chunk renderer from its blockMats, data,
        and lighting array. fills in the cr's blockRenderers with vertices
        for each block facing and material

        blockRenderers: A list to append renderers onto for how to render blocks
        """

        # chunkBlocks and chunkLights are indexed (x,z,y)
        # Get the position to render the chunk and the level containing the chunk
        cx, cz = cr.chunkPosition
        level = cr.renderer.level

        # Find the chunk that needs to be rendered
        chunk = level.getChunk(cx, cz)
        # Find the chunks that are next to the chunk to render
        neighboringChunks = self.getNeighboringChunks(chunk)

        # Find the blocks ids of the chunk with one extra block on each axis from the chunks next to it
        areaBlocks = self.getAreaBlocks(chunk, neighboringChunks)
        yield

        # Same as areaBlocks, but stores lighting values instead of block ids
        areaBlockLights = self.getAreaBlockLights(chunk, neighboringChunks)
        yield

        # Checking if there are any slabs, and if there are, set the light values of the slabs to the light value above it
        slabs = areaBlocks == pymclevel.materials.alphaMaterials.StoneSlab.ID
        if slabs.any():
            areaBlockLights[slabs] = areaBlockLights[:, :, 1:][slabs[:, :, :-1]]
        yield

        # Find which materials should be visible through solid blocks
        # facingMats maps block id to the id for the renderer for that block?
        showHiddenOres = cr.renderer.showHiddenOres
        if showHiddenOres:
            facingMats = self.hiddenOreMaterials[areaBlocks]
        else:
            facingMats = self.exposedMaterialMap[areaBlocks]

        yield

        # areaBlockMats maps block id to some renderer for that block?
        if self.roughGraphics:
            areaBlockMats = self.roughMaterials[areaBlocks]
        else:
            areaBlockMats = self.materialMap[areaBlocks]


        facingBlockIndices = self.getFacingBlockIndices(facingMats)
        yield

        # Figure out rendering geometry for the chunk, iterating through every calculation needed by computeGeometry
        for _ in self.computeGeometry(chunk, areaBlockMats, facingBlockIndices, areaBlockLights, blockRenderers):
            yield

    def computeGeometry(self, chunk: FakeChunk, areaBlockMats: np.ndarray, facingBlockIndices: list, areaBlockLights, blockRenderers):
        """
        chunk: The chunk data to compute geometry on

        areaBlockMats: A 3D array that is 2 longer than every axis as the block data

        facingBlockIndices: A list of the 6 faces, each containing a 3D array the size of the block array in the chunk, representing which blocks, via array indices for coordinates, for that face should be rendered

        areaBlockLights: Same as areaBlockMats, but indexes the light values of each block

        blockRenderers: A list to append renderers onto for how to render blocks
        """

        # Grab the block ids and their data/damage values from the chunk
        blocks, blockData = chunk.Blocks, chunk.Data
        blockData = blockData & 0xf
        # Find the block "material" id from the blocks of the original chunk
        blockMaterials = areaBlockMats[1:-1, 1:-1, 1:-1]
        # If using simple graphics, only use rendering modes 0 and 1 (empty and full block)
        if self.roughGraphics:
            blockMaterials.clip(0, 1, blockMaterials)

        # Represents indexing into the original chunk data and the chunk data expanded by one block on all sides
        sx = sz = slice(0, 16)
        asx = asz = slice(0, 18)

        # Go through every 16 block height increment of the chunk
        for y in range(0, chunk.world.Height, 16):
            # Get the indexing to get that specific height section of the chunk
            sy = slice(y, y + 16)
            asy = slice(y, y + 18)

            # Continue to compute geometry for every value needed
            for _ in self.computeCubeGeometry(
                    y,
                    blockRenderers,
                    # Use only the needed block data for this 16 tall sub section
                    blocks[sx, sz, sy], blockData[sx, sz, sy],
                    # Similarly, use only the needed material renderers
                    chunk.materials, blockMaterials[sx, sz, sy],
                    # Similarly, use the section of which blocks are facing where for this sub section
                    [f[sx, sz, sy] for f in facingBlockIndices],
                    # For the lighting, use the expanded selection
                    areaBlockLights[asx, asz, asy]
            ):
                yield

    def computeCubeGeometry(self, y, blockRenderers, blocks, blockData, materials, blockMaterials: np.ndarray, facingBlockIndices: list, areaBlockLights):
        """
        blocks: A 3D array of block ids needed to compute
        
        blockData: A 3D array of block data/damage values associated with the block ids in blocks

        materials: Object with a field for each block name and its associated block information

        blockMaterials: A 1D array indexing block id to the index of the block renderer to use for rendering that block

        facingBlockIndices: A list of the 6 faces, each containing a 3D array the size of the block array in the chunk, representing which blocks for that face should be rendered

        areaBlockLights: a 3D array of the light values for each block, expanded by one block on every axis from the given blocks
        """

        # Convert blockMaterials to a 1D array, then count how the number of occurrences of each material id
        materialCounts = np.bincount(blockMaterials.ravel())

        def texMap(blocks, blockData=0, direction=slice(None)):
            """
            returns: The textures needed for that block id in the given direction
            """
            return materials.blockTextures[blocks, blockData, direction]  # xxx slow

        # Go through each type of block renderer, figure out the index it should be using depending on if that material needs to be rendered, and add its renderer to the given list
        for blockRendererClass in self.blockRendererClasses:
            # Skip if no blocks need this renderer
            mi = blockRendererClass.materialIndex
            if mi >= len(materialCounts) or materialCounts[mi] == 0:
                continue

            # Setup the renderer, including updating its y position
            blockRenderer = blockRendererClass(self)
            blockRenderer.y = y
            blockRenderer.materials = materials
            # Figure out all vertex data needed for those blocks 
            for _ in blockRenderer.makeVertices(facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
                yield
            blockRenderers.append(blockRenderer)

            yield

    def makeTemplate(self, direction, blockIndices):
        """
        direction: The index [0, 5] of the face to get the template for
        
        blockIndices: A 3D boolean array of which block coordinates of the precomputed vertices should be included

        returns: A 1D array of the coordinates selected by blockIndices, where each element is a 4x6 array, 4 vertices, each vertex containing 6 floats representing position coordinates, texture coordinates, and color information
        """
        # Start with the (16,16,16) precomputed vertices
        # Take a subset the shape of the given indexes
        # Take only those coordinates from in the indexes
        x, z, y = blockIndices.shape
        return self.precomputedVertices[direction][:x, :z, :y][blockIndices]


class Layer:
    Blocks = "Blocks"
    Entities = "Entities"
    Monsters = "Monsters"
    Items = "Items"
    TileEntities = "TileEntities"
    TileTicks = "TileTicks"
    TerrainPopulated = "TerrainPopulated"
    AllLayers = (Blocks, Entities, Monsters, Items, TileEntities, TileTicks, TerrainPopulated)


class BlockRenderer(object):
    # vertexArrays = None
    detailLevels = (0,)
    layer = Layer.Blocks
    directionOffsets = {
        pymclevel.faces.FaceXDecreasing: np.s_[:-2, 1:-1, 1:-1],
        pymclevel.faces.FaceXIncreasing: np.s_[2:, 1:-1, 1:-1],
        pymclevel.faces.FaceYDecreasing: np.s_[1:-1, 1:-1, :-2],
        pymclevel.faces.FaceYIncreasing: np.s_[1:-1, 1:-1, 2:],
        pymclevel.faces.FaceZDecreasing: np.s_[1:-1, :-2, 1:-1],
        pymclevel.faces.FaceZIncreasing: np.s_[1:-1, 2:, 1:-1],
    }
    """
    Maps each direction to the relevant blocks of a block selection expanded by 1 block on all axes?
    """
    renderstate = ChunkCalculator.renderStateAlphaTest

    def __init__(self, cc):
        self.makeTemplate = cc.makeTemplate
        self.chunkCalculator = cc
        self.vertexArrays = []

        pass

    @classmethod
    def getBlocktypes(cls, mats):
        """
        mats: All materials that exist

        Returns: The block ids that this renderer is able draw
        """
        return cls.blocktypes

    def setAlpha(self, alpha):
        "alpha is an unsigned byte value"
        for a in self.vertexArrays:
            a.view('uint8')[_RGBA][..., 3] = alpha

    def bufferSize(self):
        return sum(a.size for a in self.vertexArrays) * 4

    def getMaterialIndices(self, blockMaterials: np.ndarray):
        """
        blockMaterials: 3D array of the block renderer ids

        returns: a 3D array of booleans, of which blocks are a material to render?
        """
        return blockMaterials == self.materialIndex

    def makeVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]

        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            vertexArray = self.makeFaceVertices(direction, materialIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap)
            yield
            if len(vertexArray):
                arrays.append(vertexArray)
        self.vertexArrays = arrays

    def makeArrayList(self, chunkPosition, showRedraw):
        l = gl.glGenLists(1)
        GL.glNewList(l, GL.GL_COMPILE)
        self.drawArrays(chunkPosition, showRedraw)
        GL.glEndList()
        return l

    def drawArrays(self, chunkPosition, showRedraw):
        cx, cz = chunkPosition
        y = 0
        if hasattr(self, 'y'):
            y = self.y
        with gl.glPushMatrix(GL.GL_MODELVIEW):
            GL.glTranslate(cx << 4, y, cz << 4)

            if showRedraw:
                GL.glColor(1.0, 0.25, 0.25, 1.0)

            self.drawVertices()

    def drawVertices(self):
        if self.vertexArrays:
            for buf in self.vertexArrays:
                self.drawFaceVertices(buf)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=np.uint8).ravel()[20:]))

        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)


class EntityRendererGeneric(BlockRenderer):
    renderstate = ChunkCalculator.renderStateEntity
    detailLevels = (0, 1, 2)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=np.uint8).ravel()[20:]))

        GL.glDepthMask(False)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

        GL.glLineWidth(2.0)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

        GL.glPolygonOffset(DepthOffset.TerrainWire, DepthOffset.TerrainWire)
        with gl.glEnable(GL.GL_POLYGON_OFFSET_FILL, GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glDepthMask(True)

    def _computeVertices(self, positions, colors, offset=False, chunkPosition=(0, 0)):
        cx, cz = chunkPosition
        x = cx << 4
        z = cz << 4

        vertexArray = np.zeros(shape=(len(positions), 6, 4, 6), dtype='float32')
        if len(positions):
            positions = np.array(positions)
            positions[:, (0, 2)] -= (x, z)
            if offset:
                positions -= 0.5

            vertexArray.view('uint8')[_RGBA] = colors
            vertexArray[_XYZ] = positions[:, np.newaxis, np.newaxis, :]
            vertexArray[_XYZ] += faceVertexTemplates[_XYZ]
            vertexArray.shape = (len(positions) * 6, 4, 6)
        return vertexArray


class TileEntityRenderer(EntityRendererGeneric):
    layer = Layer.TileEntities

    def makeChunkVertices(self, chunk: pymclevel.EntityLevel):
        tilePositions = []
        for i, ent in enumerate(chunk.TileEntities):
            if i % 10 == 0:
                yield
            if not 'x' in ent:
                continue
            tilePositions.append(pymclevel.TileEntity.pos(ent))
        tiles = self._computeVertices(tilePositions, (0xff, 0xff, 0x33, 0x44), chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [tiles]


class BaseEntityRenderer(EntityRendererGeneric):
    pass


class MonsterRenderer(BaseEntityRenderer):
    layer = Layer.Entities  # xxx Monsters
    notMonsters = set(["Item", "XPOrb", "Painting"])

    def makeChunkVertices(self, chunk: pymclevel.EntityLevel):
        monsterPositions = []
        for i, ent in enumerate(chunk.Entities):
            if i % 10 == 0:
                yield
            id = ent["id"].value
            if id in self.notMonsters:
                continue

            monsterPositions.append(pymclevel.Entity.pos(ent))

        monsters = self._computeVertices(monsterPositions,
                                         (0xff, 0x22, 0x22, 0x44),
                                         offset=True,
                                         chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [monsters]


class EntityRenderer(BaseEntityRenderer):
    def makeChunkVertices(self, chunk: pymclevel.EntityLevel):
        yield
#        entityPositions = []
#        for i, ent in enumerate(chunk.Entities):
#            if i % 10 == 0:
#                yield
#            entityPositions.append(pymclevel.Entity.pos(ent))
#
#        entities = self._computeVertices(entityPositions, (0x88, 0x00, 0x00, 0x66), offset=True, chunkPosition=chunk.chunkPosition)
#        yield
#        self.vertexArrays = [entities]


class ItemRenderer(BaseEntityRenderer):
    layer = Layer.Items

    def makeChunkVertices(self, chunk: pymclevel.EntityLevel):
        entityPositions = []
        entityColors = []
        colorMap = {
            "Item": (0x22, 0xff, 0x22, 0x5f),
            "XPOrb": (0x88, 0xff, 0x88, 0x5f),
            "Painting": (134, 96, 67, 0x5f),
        }
        for i, ent in enumerate(chunk.Entities):
            if i % 10 == 0:
                yield
            color = colorMap.get(ent["id"].value)
            if color is None:
                continue

            entityPositions.append(pymclevel.Entity.pos(ent))
            entityColors.append(color)

        entities = self._computeVertices(entityPositions, np.array(entityColors, dtype='uint8')[:, np.newaxis, np.newaxis], offset=True, chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [entities]


class TileTicksRenderer(EntityRendererGeneric):
    layer = Layer.TileTicks

    def makeChunkVertices(self, chunk: pymclevel.MCChunk):
        chunk.decompress()
        if chunk.root_tag and "Level" in chunk.root_tag and "TileTicks" in chunk.root_tag["Level"]:
            ticks = chunk.root_tag["Level"]["TileTicks"]
            if len(ticks):
                self.vertexArrays.append(self._computeVertices([[t[i].value for i in "xyz"] for t in ticks],
                                                               (0xff, 0xff, 0xff, 0x44),
                                                               chunkPosition=chunk.chunkPosition))

        yield


class TerrainPopulatedRenderer(EntityRendererGeneric):
    layer = Layer.TerrainPopulated
    vertexTemplate = np.zeros((6, 4, 6), 'float32')
    vertexTemplate[_XYZ] = faceVertexTemplates[_XYZ]
    vertexTemplate[_XYZ] *= (16, 128, 16)
    color = (255, 200, 155)
    vertexTemplate.view('uint8')[_RGBA] = color + (72,)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=np.uint8).ravel()[20:]))

        GL.glDepthMask(False)

        # GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glDisable(GL.GL_CULL_FACE)

        with gl.glEnable(GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)

        GL.glEnable(GL.GL_CULL_FACE)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

        GL.glLineWidth(1.0)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glLineWidth(2.0)
        with gl.glEnable(GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glLineWidth(1.0)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glDepthMask(True)

#        GL.glPolygonOffset(DepthOffset.TerrainWire, DepthOffset.TerrainWire)
#        with gl.glEnable(GL.GL_POLYGON_OFFSET_FILL, GL.GL_DEPTH_TEST):
#            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
#

    def makeChunkVertices(self, chunk):
        chunk.decompress()
        neighbors = self.chunkCalculator.getNeighboringChunks(chunk)

        def getpop(ch):
            return getattr(ch, "TerrainPopulated", True)

        pop = getpop(chunk)
        yield
        if pop:
            return

        visibleFaces = [
            getpop(neighbors[pymclevel.faces.FaceXIncreasing]),
            getpop(neighbors[pymclevel.faces.FaceXDecreasing]),
            True,
            True,
            getpop(neighbors[pymclevel.faces.FaceZIncreasing]),
            getpop(neighbors[pymclevel.faces.FaceZDecreasing]),
        ]
        visibleFaces = np.array(visibleFaces, dtype='bool')
        verts = self.vertexTemplate[visibleFaces]
        self.vertexArrays.append(verts)

        yield


class LowDetailBlockRenderer(BlockRenderer):
    renderstate = ChunkCalculator.renderStateLowDetail
    detailLevels = (1,)

    def drawFaceVertices(self, buf):
        if not len(buf):
            return
        stride = 16

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, np.ravel(buf.ravel()))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype='uint8').ravel()[12:]))

        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    def makeChunkVertices(self, ch: pymclevel.ChunkBase):
        step: int = 1

        level = ch.world
        vertexArrays = []
        blocks = ch.Blocks
        heightMap = ch.HeightMap

        # Copy the height map and blocks from the chunk
        heightMap = heightMap[::step, ::step]
        blocks = blocks[::step, ::step]

        # Do nothing if any of the dimensions in the blocks of the chunk are empty
        if 0 in blocks.shape:
            return

        # Grab the size of the chunk, 16x16x128
        chunkWidth, chunkLength, chunkHeight = blocks.shape
        # Build a chunk of zeros, 16x16x128 of all zeros
        blockIndices = np.zeros((chunkWidth, chunkLength, chunkHeight), bool)

        # Build the indexes of the x and z coordinates
        # grid_axes will be a list of two elements, the first element is a 2D array of the x coordinates of every block, the second element is the same for the z coordinates
        grid_axes = list(np.indices((chunkWidth, chunkLength)))

        # Building a height map
        # Subtract one from every height, then swap the axes
        # This brings the height coordinates to array indexes and swaps the (z, x) height map to be (x, z)
        h = np.swapaxes(heightMap - 1, 0, 1)[:chunkWidth, :chunkLength]
        # Clamp every height in the height map to be in the range [0, 127]
        np.clip(h, 0, chunkHeight - 1, out=h)

        # Build a list of coordinates
        # The list is all the x coordinates, all the z coordinates, then the transformed height map
        grid_axes: list[np.ndarray[np.ndarray]] = [grid_axes[0], grid_axes[1], h]

        # Setup a 2D array, 16x16 of all zeros
        depths = np.zeros((chunkWidth, chunkLength), dtype='uint16')
        # TODO what is this doing? Seems to be taking a subset of the height map
        depths[1:-1, 1:-1] = reduce(np.minimum, (h[1:-1, :-2], h[1:-1, 2:], h[:-2, 1:-1]), h[2:, 1:-1])
        yield

        try:
            grid_axes = tuple(grid_axes)
            # Get an (x, z) indexed array of the highest block in each (x, z) coordinate of the chunk
            topBlocks = blocks[grid_axes]
            nonAirBlocks = (topBlocks != 0)
            blockIndices[grid_axes] = nonAirBlocks
            h += 1
            np.clip(h, 0, chunkHeight - 1, out=h)
            over_blocks = blocks[grid_axes][nonAirBlocks].ravel()

        except ValueError as e:
            traceback.print_exc()
            raise ValueError(str(e.args) + "Chunk shape: {0}".format(blockIndices.shape), sys.exc_info()[-1])

        if nonAirBlocks.any():
            blockTypes = blocks[blockIndices]

            flat_colors = level.materials.flatColors[blockTypes, ch.Data[blockIndices] & 0xf][:, np.newaxis, :]
            x, z, y = blockIndices.nonzero()

            yield
            vertexArray = np.zeros((len(x), 4, 4), dtype='float32')
            vertexArray[_XYZ][..., 0] = x[:, np.newaxis]
            vertexArray[_XYZ][..., 1] = y[:, np.newaxis]
            vertexArray[_XYZ][..., 2] = z[:, np.newaxis]

            va0 = np.array(vertexArray)

            va0[..., :3] += faceVertexTemplates[pymclevel.faces.FaceYIncreasing, ..., :3]

            over_mask = over_blocks > 0
            flat_colors[over_mask] = level.materials.flatColors[:, 0][over_blocks[over_mask]][:, np.newaxis]

            if self.detailLevel == 2:
                height_factor = (y / float(2.0 * ch.world.Height)) + 0.5
                flat_colors[..., :3] = (flat_colors[..., :3].astype(np.float64) * height_factor[:, np.newaxis, np.newaxis]).astype(np.uint8)

            _RGBA = np.s_[..., 12:16]
            va0.view('uint8')[_RGBA] = flat_colors

            va0[_XYZ][:, :, 0] *= step
            va0[_XYZ][:, :, 2] *= step

            yield
            if self.detailLevel == 2:
                self.vertexArrays = [va0]
                return

            va1 = np.array(vertexArray)
            va1[..., :3] += faceVertexTemplates[pymclevel.faces.FaceXIncreasing, ..., :3]

            va1[_XYZ][:, (0, 1), 1] = depths[nonAirBlocks].ravel()[:, np.newaxis]  # stretch to floor
            va1[_XYZ][:, (1, 2), 0] -= 1.0  # turn diagonally
            va1[_XYZ][:, (2, 3), 1] -= 0.5  # drop down to prevent intersection pixels

            va1[_XYZ][:, :, 0] *= step
            va1[_XYZ][:, :, 2] *= step

            # Darken the colors
            flat_colors = (flat_colors * 0.8).astype(np.uint8)

            va1.view('uint8')[_RGBA] = flat_colors
            grassmask = topBlocks[nonAirBlocks] == 2
            # color grass sides with dirt's color
            va1.view('uint8')[_RGBA][grassmask] = level.materials.flatColors[:, 0][[3]][:, np.newaxis]

            va2 = np.array(va1)
            va2[_XYZ][:, (1, 2), 0] += step
            va2[_XYZ][:, (0, 3), 0] -= step

            vertexArrays = [va1, va2, va0]

        self.vertexArrays = vertexArrays


class OverheadBlockRenderer(LowDetailBlockRenderer):
    detailLevels = (2,)


class GenericBlockRenderer(BlockRenderer):
    renderstate = ChunkCalculator.renderStateAlphaTest

    materialIndex = 1

    def makeGenericVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        """
        facingBlockIndices: A array of each of the 6 faces, each array element containing a 3D boolean array of which faces at which positions via indices are exposed to air

        blocks: A 3D array of the block ids at each position

        blockMaterials: a 3D array of the "renderer" id to use for each block

        blockData: a 3D array of the data/damage value of each block

        areaBlockLights: a 3D array of the light values for each block, expanded by one block on every axis from the given blocks

        texMap: Texture data for the blocks
        """

        vertexArrays = []
        # Finding a boolean mask for how blocks should be rendered?
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        # For each of the 6 edges of the blocks, compute vertex data
        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            # Find the light levels of the blocks on that face of the given blocks?
            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            # Find a boolean mask of the blocks that have exposed faces, and also match some boolean condition for rendering the material?
            blockIndices = materialIndices & exposedFaceIndices

            # Find a 1D array of the block coordinates that need to be rendered?
            theseBlocks = blocks[blockIndices]
            # The same but for the data/damage value
            bdata = blockData[blockIndices]

            # Use the precomputed vertex data to make the actual vertex array
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            def setTexture():
                vertexArray[_ST] += texMap(theseBlocks, bdata, direction)[:, np.newaxis, 0:2]
            setTexture()

            def setGrassColors():
                grass = theseBlocks == pymclevel.materials.alphaMaterials.Grass.ID
                vertexArray.view('uint8')[_RGB][grass] = (vertexArray.view('uint8')[_RGB][grass] * self.grassColor).astype(np.uint8)

            def getBlockLight():
                return facingBlockLight[blockIndices]

            def setColors():
                vertexArray.view('uint8')[_RGB] *= getBlockLight()[..., np.newaxis, np.newaxis]
                if self.materials.name in ("Alpha"):
                    if direction == pymclevel.faces.FaceYIncreasing:
                        setGrassColors()
                # leaves = theseBlocks == pymclevel.materials.alphaMaterials.Leaves.ID
                # vertexArray.view('uint8')[_RGBA][leaves] *= [0.15, 0.88, 0.15, 1.0]
#                snow = theseBlocks == pymclevel.materials.alphaMaterials.SnowLayer.ID
#                if direction == pymclevel.faces.FaceYIncreasing:
#                    vertexArray[_XYZ][snow, ...,1] -= 0.875
#
#                if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
#                    vertexArray[_XYZ][snow, ...,2:4,1] -= 0.875
#                    vertexArray[_ST][snow, ...,2:4,1] += 14
#
            setColors()
            yield

            vertexArrays.append(vertexArray)

        self.vertexArrays = vertexArrays

    grassColor = grassColorDefault = [0.39, 0.77, 0.23]  # 62C743

    makeVertices = makeGenericVertices


class LeafBlockRenderer(BlockRenderer):
    blocktypes = [18]

    @property
    def renderstate(self):
        if self.chunkCalculator.fastLeaves:
            return ChunkCalculator.renderStatePlain
        else:
            return ChunkCalculator.renderStateAlphaTest

    def makeLeafVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        if self.materials.name in ("Alpha"):
            if not self.chunkCalculator.fastLeaves:
                blockIndices = materialIndices
                data = blockData[blockIndices]
                data &= 0x3  # ignore decay states
                leaves = (data == 0) | (data == 3)
                pines = (data == pymclevel.materials.alphaMaterials.PineLeaves.blockData)
                birches = (data == pymclevel.materials.alphaMaterials.BirchLeaves.blockData)
                texes = texMap(18, data, 0)
        else:
            blockIndices = materialIndices
            texes = texMap(18, [0], 0)

        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            if self.materials.name in ("Alpha"):
                if self.chunkCalculator.fastLeaves:
                    blockIndices = materialIndices & exposedFaceIndices
                    data = blockData[blockIndices]
                    data &= 0x3  # ignore decay states
                    leaves = (data == 0)
                    pines = (data == pymclevel.materials.alphaMaterials.PineLeaves.blockData)
                    birches = (data == pymclevel.materials.alphaMaterials.BirchLeaves.blockData)
                    type3 = (data == 3)
                    leaves |= type3

                    texes = texMap(18, data, 0)

            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            vertexArray[_ST] += texes[:, np.newaxis]

            if not self.chunkCalculator.fastLeaves:
                vertexArray[_ST] -= (0x10, 0x0)

            vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., np.newaxis, np.newaxis]
            if self.materials.name in ("Alpha"):
                vertexArray.view('uint8')[_RGB][leaves] = (vertexArray.view('uint8')[_RGB][leaves] * self.leafColor).astype(np.uint8)
                vertexArray.view('uint8')[_RGB][pines] = (vertexArray.view('uint8')[_RGB][pines] * self.pineLeafColor).astype(np.uint8)
                vertexArray.view('uint8')[_RGB][birches] = (vertexArray.view('uint8')[_RGB][birches] * self.birchLeafColor).astype(np.uint8)

            yield
            arrays.append(vertexArray)

        self.vertexArrays = arrays

    leafColor = leafColorDefault = [0x48 / 255., 0xb5 / 255., 0x18 / 255.]  # 48b518
    pineLeafColor = pineLeafColorDefault = [0x61 / 255., 0x99 / 255., 0x61 / 255.]  # 0x619961
    birchLeafColor = birchLeafColorDefault = [0x80 / 255., 0xa7 / 255., 0x55 / 255.]  # 0x80a755

    makeVertices = makeLeafVertices


class PlantBlockRenderer(BlockRenderer):
    @classmethod
    def getBlocktypes(cls, mats):
        # Plant block types are any block ids where their type is one of the below types of blocks for how they're rendered

        # blocktypes = [6, 37, 38, 39, 40, 59, 83]
        # if mats.name != "Classic": blocktypes += [31, 32]  # shrubs, tall grass
        # if mats.name == "Alpha": blocktypes += [115]  # nether wart
        blocktypes = [b.ID for b in mats if b.type in ("DECORATION_CROSS", "NETHER_WART", "CROPS", "STEM")]

        return blocktypes

    renderstate = ChunkCalculator.renderStateAlphaTest

    def makePlantVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield

        theseBlocks = blocks[blockIndices]

        bdata = blockData[blockIndices]
        bdata[theseBlocks == 6] &= 0x3  # xxx saplings only
        texes = texMap(blocks[blockIndices], bdata, 0)

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        lights = blockLight[blockIndices][..., np.newaxis, np.newaxis]

        colorize = None
        if self.materials.name == "Alpha":
            colorize = (theseBlocks == pymclevel.materials.alphaMaterials.TallGrass.ID) & (bdata != 0)

        for direction in (pymclevel.faces.FaceXIncreasing, pymclevel.faces.FaceXDecreasing, pymclevel.faces.FaceZIncreasing, pymclevel.faces.FaceZDecreasing):
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                return

            if direction == pymclevel.faces.FaceXIncreasing:
                vertexArray[_XYZ][..., 1:3, 0] -= 1
            if direction == pymclevel.faces.FaceXDecreasing:
                vertexArray[_XYZ][..., 1:3, 0] += 1
            if direction == pymclevel.faces.FaceZIncreasing:
                vertexArray[_XYZ][..., 1:3, 2] -= 1
            if direction == pymclevel.faces.FaceZDecreasing:
                vertexArray[_XYZ][..., 1:3, 2] += 1

            vertexArray[_ST] += texes[:, np.newaxis, 0:2]

            vertexArray.view('uint8')[_RGBA] = 0xf  # ignore precomputed directional light
            vertexArray.view('uint8')[_RGB] *= lights
            if colorize is not None:
                vertexArray.view('uint8')[_RGB][colorize] = (vertexArray.view('uint8')[_RGB][colorize] * LeafBlockRenderer.leafColor).astype(np.uint8)

            arrays.append(vertexArray)
            yield

        self.vertexArrays = arrays

    makeVertices = makePlantVertices


class TorchBlockRenderer(BlockRenderer):
    blocktypes = [50, 75, 76]
    renderstate = ChunkCalculator.renderStateAlphaTest
    torchOffsetsStraight = [
        [  # FaceXIncreasing
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
        ],
        [  # FaceXDecreasing
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
        ],
        [  # FaceYIncreasing
            (7 / 16., -6 / 16., 7 / 16.),
            (7 / 16., -6 / 16., -7 / 16.),
            (-7 / 16., -6 / 16., -7 / 16.),
            (-7 / 16., -6 / 16., 7 / 16.),
        ],
        [  # FaceYDecreasing
            (7 / 16., 0., 7 / 16.),
            (-7 / 16., 0., 7 / 16.),
            (-7 / 16., 0., -7 / 16.),
            (7 / 16., 0., -7 / 16.),
        ],

        [  # FaceZIncreasing
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.)
        ],
        [  # FaceZDecreasing
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.)
        ],

    ]

    torchOffsetsSouth = [
        [  # FaceXIncreasing
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
        ],
        [  # FaceXDecreasing
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
        ],
        [  # FaceYIncreasing
            (7 / 16., -3 / 16., 7 / 16.),
            (7 / 16., -3 / 16., -7 / 16.),
            (-7 / 16., -3 / 16., -7 / 16.),
            (-7 / 16., -3 / 16., 7 / 16.),
        ],
        [  # FaceYDecreasing
            (7 / 16., 3 / 16., 7 / 16.),
            (-7 / 16., 3 / 16., 7 / 16.),
            (-7 / 16., 3 / 16., -7 / 16.),
            (7 / 16., 3 / 16., -7 / 16.),
        ],

        [  # FaceZIncreasing
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.)
        ],
        [  # FaceZDecreasing
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
        ],

    ]
    torchOffsetsNorth = torchOffsetsWest = torchOffsetsEast = torchOffsetsSouth

    torchOffsets = [
        torchOffsetsStraight,
        torchOffsetsSouth,
        torchOffsetsNorth,
        torchOffsetsWest,
        torchOffsetsEast,
        torchOffsetsStraight,
    ] + [torchOffsetsStraight] * 10

    torchOffsets = np.array(torchOffsets, dtype='float32')

    torchOffsets[1][..., 3, :, 0] -= 0.5

    torchOffsets[1][..., 0:2, 0:2, 0] -= 0.5
    torchOffsets[1][..., 4:6, 0:2, 0] -= 0.5
    torchOffsets[1][..., 0:2, 2:4, 0] -= 0.1
    torchOffsets[1][..., 4:6, 2:4, 0] -= 0.1

    torchOffsets[1][..., 2, :, 0] -= 0.25

    torchOffsets[2][..., 3, :, 0] += 0.5
    torchOffsets[2][..., 0:2, 0:2, 0] += 0.5
    torchOffsets[2][..., 4:6, 0:2, 0] += 0.5
    torchOffsets[2][..., 0:2, 2:4, 0] += 0.1
    torchOffsets[2][..., 4:6, 2:4, 0] += 0.1
    torchOffsets[2][..., 2, :, 0] += 0.25

    torchOffsets[3][..., 3, :, 2] -= 0.5
    torchOffsets[3][..., 0:2, 0:2, 2] -= 0.5
    torchOffsets[3][..., 4:6, 0:2, 2] -= 0.5
    torchOffsets[3][..., 0:2, 2:4, 2] -= 0.1
    torchOffsets[3][..., 4:6, 2:4, 2] -= 0.1
    torchOffsets[3][..., 2, :, 2] -= 0.25

    torchOffsets[4][..., 3, :, 2] += 0.5
    torchOffsets[4][..., 0:2, 0:2, 2] += 0.5
    torchOffsets[4][..., 4:6, 0:2, 2] += 0.5
    torchOffsets[4][..., 0:2, 2:4, 2] += 0.1
    torchOffsets[4][..., 4:6, 2:4, 2] += 0.1
    torchOffsets[4][..., 2, :, 2] += 0.25

    upCoords = ((7, 6), (7, 8), (9, 8), (9, 6))
    downCoords = ((7, 14), (7, 16), (9, 16), (9, 14))

    def makeTorchVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        torchOffsets = self.torchOffsets[blockData[blockIndices]]
        texes = texMap(blocks[blockIndices], blockData[blockIndices])
        yield
        arrays = []
        for direction in range(6):
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                return

            vertexArray.view('uint8')[_RGBA] = 0xff
            vertexArray[_XYZ] += torchOffsets[:, direction]
            if direction == pymclevel.faces.FaceYIncreasing:
                vertexArray[_ST] = self.upCoords
            if direction == pymclevel.faces.FaceYDecreasing:
                vertexArray[_ST] = self.downCoords
            vertexArray[_ST] += texes[:, np.newaxis, direction]
            arrays.append(vertexArray)
            yield
        self.vertexArrays = arrays

    makeVertices = makeTorchVertices


class RailBlockRenderer(BlockRenderer):
    blocktypes = [pymclevel.materials.alphaMaterials.Rail.ID, pymclevel.materials.alphaMaterials.PoweredRail.ID, pymclevel.materials.alphaMaterials.DetectorRail.ID]
    renderstate = ChunkCalculator.renderStateAlphaTest

    railTextures = np.array([
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # east-west
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # north-south
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # south-ascending
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # north-ascending
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # east-ascending
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # west-ascending

        [(0, 112), (0, 128), (16, 128), (16, 112)],  # northeast corner
        [(0, 128), (16, 128), (16, 112), (0, 112)],  # southeast corner
        [(16, 128), (16, 112), (0, 112), (0, 128)],  # southwest corner
        [(16, 112), (0, 112), (0, 128), (16, 128)],  # northwest corner

        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown

    ], dtype='float32')
    railTextures -= pymclevel.materials.alphaMaterials.blockTextures[pymclevel.materials.alphaMaterials.Rail.ID, 0, 0]

    railOffsets = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],

        [0, 0, 1, 1],  # south-ascending
        [1, 1, 0, 0],  # north-ascending
        [1, 0, 0, 1],  # east-ascending
        [0, 1, 1, 0],  # west-ascending

        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],

        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],

    ], dtype='float32')

    def makeRailVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        direction = pymclevel.faces.FaceYIncreasing
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield

        bdata = blockData[blockIndices]
        railBlocks = blocks[blockIndices]
        tex = texMap(railBlocks, bdata, pymclevel.faces.FaceYIncreasing)[:, np.newaxis, :]

        # disable 'powered' or 'pressed' bit for powered and detector rails
        bdata[railBlocks != pymclevel.materials.alphaMaterials.Rail.ID] &= 0xF7

        vertexArray = self.makeTemplate(direction, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] = self.railTextures[bdata]
        vertexArray[_ST] += tex

        vertexArray[_XYZ][..., 1] -= 0.9
        vertexArray[_XYZ][..., 1] += self.railOffsets[bdata]

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]

        vertexArray.view('uint8')[_RGB] *= blockLight[blockIndices][..., np.newaxis, np.newaxis]
        yield
        self.vertexArrays = [vertexArray]

    makeVertices = makeRailVertices


class LadderBlockRenderer(BlockRenderer):
    blocktypes = [pymclevel.materials.alphaMaterials.Ladder.ID]

    ladderOffsets = np.array([
        [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
        [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],

        [(0, -1, 0.9), (0, 0, -0.1), (0, 0, -0.1), (0, -1, 0.9)],  # facing east
        [(0, 0, 0.1), (0, -1, -.9), (0, -1, -.9), (0, 0, 0.1)],  # facing west
        [(.9, -1, 0), (.9, -1, 0), (-.1, 0, 0), (-.1, 0, 0)],  # north
        [(0.1, 0, 0), (0.1, 0, 0), (-.9, -1, 0), (-.9, -1, 0)],  # south

    ] + [[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]] * 10, dtype='float32')

    ladderTextures = np.array([
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown

        [(64, 96), (64, 80), (48, 80), (48, 96), ],  # e
        [(48, 80), (48, 96), (64, 96), (64, 80), ],  # w
        [(48, 96), (64, 96), (64, 80), (48, 80), ],  # n
        [(64, 80), (48, 80), (48, 96), (64, 96), ],  # s

        ] + [[(0, 192), (0, 208), (16, 208), (16, 192)]] * 10, dtype='float32')

    def ladderVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        yield
        bdata = blockData[blockIndices]

        vertexArray = self.makeTemplate(pymclevel.faces.FaceYIncreasing, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] = self.ladderTextures[bdata]
        vertexArray[_XYZ] += self.ladderOffsets[bdata]
        vertexArray.view('uint8')[_RGB] *= blockLight[blockIndices][..., np.newaxis, np.newaxis]

        yield
        self.vertexArrays = [vertexArray]

    makeVertices = ladderVertices


class SnowBlockRenderer(BlockRenderer):
    snowID = 78

    blocktypes = [snowID]

    def makeSnowVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        snowIndices = self.getMaterialIndices(blockMaterials)
        arrays = []
        yield
        for direction, exposedFaceIndices in enumerate(facingBlockIndices):
    # def makeFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        # return []

            if direction != pymclevel.faces.FaceYIncreasing:
                blockIndices = snowIndices & exposedFaceIndices
            else:
                blockIndices = snowIndices

            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            lights = facingBlockLight[blockIndices][..., np.newaxis, np.newaxis]

            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            vertexArray[_ST] += texMap([self.snowID], 0, 0)[:, np.newaxis, 0:2]
            vertexArray.view('uint8')[_RGB] *= lights

            if direction == pymclevel.faces.FaceYIncreasing:
                vertexArray[_XYZ][..., 1] -= 0.875

            if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
                vertexArray[_XYZ][..., 2:4, 1] -= 0.875
                vertexArray[_ST][..., 2:4, 1] += 14

            arrays.append(vertexArray)
            yield
        self.vertexArrays = arrays

    makeVertices = makeSnowVertices


class RedstoneBlockRenderer(BlockRenderer):
    blocktypes = [55]

    def redstoneVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield
        vertexArray = self.makeTemplate(pymclevel.faces.FaceYIncreasing, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] += pymclevel.materials.alphaMaterials.blockTextures[55, 0, 0]
        vertexArray[_XYZ][..., 1] -= 0.9

        bdata = blockData[blockIndices]

        bdata <<= 3
        # bdata &= 0xe0
        bdata[bdata > 0] |= 0x80

        vertexArray.view('uint8')[_RGBA][..., 0] = bdata[..., np.newaxis]
        vertexArray.view('uint8')[_RGBA][..., 1:3] = 0

        yield
        self.vertexArrays = [vertexArray]

    makeVertices = redstoneVertices

# button, floor plate, door -> 1-cube features


class FeatureBlockRenderer(BlockRenderer):
#    blocktypes = [pymclevel.materials.alphaMaterials.Button.ID,
#                  pymclevel.materials.alphaMaterials.StoneFloorPlate.ID,
#                  pymclevel.materials.alphaMaterials.WoodFloorPlate.ID,
#                  pymclevel.materials.alphaMaterials.WoodenDoor.ID,
#                  pymclevel.materials.alphaMaterials.IronDoor.ID,
#                  ]
#
    blocktypes = [pymclevel.materials.alphaMaterials.Fence.ID]

    buttonOffsets = [
        [[-14 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
        ],
        [[0 / 16., 6 / 16., 5 / 16.],
         [0 / 16., 6 / 16., -5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
         [0 / 16., -7 / 16., 5 / 16.],
        ],

        [[0 / 16., -7 / 16., 5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
        ],
        [[0 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., 6 / 16., -5 / 16.],
         [0 / 16., 6 / 16., -5 / 16.],
        ],

        [[0 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
        ],
        [[-14 / 16., 6 / 16., 5 / 16.],
         [0 / 16., 6 / 16., 5 / 16.],
         [0 / 16., -7 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
        ],
    ]
    buttonOffsets = np.array(buttonOffsets)
    buttonOffsets[buttonOffsets < 0] += 1.0

    dirIndexes = ((3, 2), (-3, 2), (1, 3), (1, 3), (-1, 2), (1, 2))

    def buttonVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = blocks == pymclevel.materials.alphaMaterials.Button.ID
        axes = blockIndices.nonzero()

        vertexArray = np.zeros((len(axes[0]), 6, 4, 6), dtype=np.float32)
        vertexArray[_XYZ][..., 0] = axes[0][..., np.newaxis, np.newaxis]
        vertexArray[_XYZ][..., 1] = axes[2][..., np.newaxis, np.newaxis]
        vertexArray[_XYZ][..., 2] = axes[1][..., np.newaxis, np.newaxis]

        vertexArray[_XYZ] += self.buttonOffsets
        vertexArray[_ST] = [[0, 0], [0, 16], [16, 16], [16, 0]]
        vertexArray[_ST] += texMap(pymclevel.materials.alphaMaterials.Stone.ID, 0)[np.newaxis, :, np.newaxis]

        # if direction == 0:
#        for i, j in enumerate(self.dirIndexes[direction]):
#                if j < 0:
#                    j = -j
#                    j -= 1
#                    offs = self.buttonOffsets[direction, ..., j] * 16
#                    offs = 16 - offs
#
#                else:
#                    j -= 1
#                    offs =self.buttonOffsets[direction, ..., j] * 16
#
#                # if i == 1:
#                #
#                #    vertexArray[_ST][...,i] -= offs
#                # else:
#                vertexArray[_ST][...,i] -= offs
#
        vertexArray.view('uint8')[_RGB] = 255
        vertexArray.shape = (len(axes[0]) * 6, 4, 6)

        self.vertexArrays = [vertexArray]

    fenceTemplates = makeVertexTemplates(3 / 8., 0, 3 / 8., 5 / 8., 1, 5 / 8.)

    def fenceVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        fenceMask = blocks == pymclevel.materials.alphaMaterials.Fence.ID
        fenceIndices = fenceMask.nonzero()
        yield

        vertexArray = np.zeros((len(fenceIndices[0]), 6, 4, 6), dtype='float32')
        for i in range(3):
            j = (0, 2, 1)[i]

            vertexArray[..., i] = fenceIndices[j][:, np.newaxis, np.newaxis]  # xxx swap z with y using ^

        vertexArray[..., 0:5] += self.fenceTemplates[..., 0:5]
        vertexArray[_ST] += pymclevel.materials.alphaMaterials.blockTextures[pymclevel.materials.alphaMaterials.WoodPlanks.ID, 0, 0]

        vertexArray.view('uint8')[_RGBA] = self.fenceTemplates[..., 5][..., np.newaxis]

        vertexArray.view('uint8')[_RGB] *= areaBlockLights[1:-1, 1:-1, 1:-1][fenceIndices][..., np.newaxis, np.newaxis, np.newaxis]
        vertexArray.shape = (vertexArray.shape[0] * 6, 4, 6)
        yield
        self.vertexArrays = [vertexArray]

    makeVertices = fenceVertices


class StairBlockRenderer(BlockRenderer):
    @classmethod
    def getBlocktypes(cls, mats):
        # Renders specifically blocks that are stairs
        return [a.ID for a in mats.AllStairs]

    # South - FaceXIncreasing
    # North - FaceXDecreasing
    # West - FaceZIncreasing
    # East - FaceZDecreasing
    stairTemplates = np.array([makeVertexTemplates(**kw) for kw in [
        # South - FaceXIncreasing
        {"xmin":0.5},
        # North - FaceXDecreasing
        {"xmax":0.5},
        # West - FaceZIncreasing
        {"zmin":0.5},
        # East - FaceZDecreasing
        {"zmax":0.5},
        # Slabtype
        {"ymax":0.5},
        ]
    ])

    def stairVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield
        stairBlocks = blocks[materialIndices]
        stairData = blockData[materialIndices] & 0x3

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        x, z, y = materialIndices.nonzero()

        for _ in ("slab", "step"):
            vertexArray = np.zeros((len(x), 6, 4, 6), dtype='float32')
            for i in range(3):
                vertexArray[_XYZ][..., i] = (x, y, z)[i][:, np.newaxis, np.newaxis]

            if _ == "step":
                vertexArray[_XYZST] += self.stairTemplates[4][..., :5]

            else:
                vertexArray[_XYZST] += self.stairTemplates[stairData][..., :5]

            vertexArray[_ST] += texMap(stairBlocks, 0)[..., np.newaxis, :]

            vertexArray.view('uint8')[_RGB] = self.stairTemplates[4][np.newaxis, ..., 5, np.newaxis]
            vertexArray.view('uint8')[_RGB] *= 0xf
            vertexArray.view('uint8')[_A] = 0xff

            vertexArray.shape = (len(x) * 6, 4, 6)
            yield
            arrays.append(vertexArray)
        self.vertexArrays = arrays

    makeVertices = stairVertices


class SlabBlockRenderer(BlockRenderer):
    slabID = 44
    blocktypes = [slabID]

    def slabFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        if direction != pymclevel.faces.FaceYIncreasing:
            blockIndices = blockIndices & exposedFaceIndices

        lights = facingBlockLight[blockIndices][..., np.newaxis, np.newaxis]
        bdata = blockData[blockIndices]

        vertexArray = self.makeTemplate(direction, blockIndices)
        if not len(vertexArray):
            return vertexArray

        vertexArray[_ST] += texMap(self.slabID, bdata, direction)[:, np.newaxis, 0:2]
        vertexArray.view('uint8')[_RGB] *= lights

        if direction == pymclevel.faces.FaceYIncreasing:
            vertexArray[_XYZ][..., 1] -= 0.5

        if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
            vertexArray[_XYZ][..., 2:4, 1] -= 0.5
            vertexArray[_ST][..., 2:4, 1] += 8

        return vertexArray

    makeFaceVertices = slabFaceVertices


class WaterBlockRenderer(BlockRenderer):
    waterID = 9
    blocktypes = [8, waterID]
    renderstate = ChunkCalculator.renderStateWater

    def waterFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        blockIndices = blockIndices & exposedFaceIndices
        vertexArray = self.makeTemplate(direction, blockIndices)
        vertexArray[_ST] += texMap(self.waterID, 0, 0)[np.newaxis, np.newaxis]
        vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., np.newaxis, np.newaxis]
        return vertexArray

    makeFaceVertices = waterFaceVertices


class IceBlockRenderer(BlockRenderer):
    iceID = 79
    blocktypes = [iceID]
    renderstate = ChunkCalculator.renderStateIce

    def iceFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        blockIndices = blockIndices & exposedFaceIndices
        vertexArray = self.makeTemplate(direction, blockIndices)
        vertexArray[_ST] += texMap(self.iceID, 0, 0)[np.newaxis, np.newaxis]
        vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., np.newaxis, np.newaxis]
        return vertexArray

    makeFaceVertices = iceFaceVertices

from glutils import DisplayList


class MCRenderer(object):
    isPreviewer = False

    def __init__(self, level: pymclevel.MCLevel=None, alpha=1.0):
        self.render = True
        self.origin = (0, 0, 0)
        self.rotation = 0

        self.bufferUsage = 0

        self.invalidChunkQueue = deque()
        self._chunkWorker = None
        self.chunkRenderers = {}
        self.loadableChunkMarkers = DisplayList()
        self.visibleLayers = set(Layer.AllLayers)

        self.masterLists = None

        alpha = alpha * 255
        self.alpha = (int(alpha) & 0xff)

        self.chunkStartTime = datetime.now()
        self.oldChunkStartTime = self.chunkStartTime

        self.oldPosition = None

        self.chunkSamples = [timedelta(0, 0, 0)] * 15

        self.chunkIterator = None

        import leveleditor
        Settings = leveleditor.Settings

        Settings.fastLeaves.addObserver(self)

        Settings.roughGraphics.addObserver(self)
        Settings.showHiddenOres.addObserver(self)
        Settings.vertexBufferLimit.addObserver(self)

        Settings.drawEntities.addObserver(self)
        Settings.drawTileEntities.addObserver(self)
        Settings.drawTileTicks.addObserver(self)
        Settings.drawUnpopulatedChunks.addObserver(self, "drawTerrainPopulated")
        Settings.drawMonsters.addObserver(self)
        Settings.drawItems.addObserver(self)

        Settings.showChunkRedraw.addObserver(self, "showRedraw")
        Settings.spaceHeight.addObserver(self)
        Settings.targetFPS.addObserver(self, "targetFPS")

        self.level: pymclevel.MCLevel = level

        self.overheadMode: bool
        """ true if rendering the overview from on top of the world, false for normal 3D look around rendering """

    chunkClass = ChunkRenderer
    calculatorClass = ChunkCalculator

    minViewDistance = 2
    maxViewDistance = 64

    _viewDistance = 16

    needsRedraw = True

    def toggleLayer(self, val, layer):
        if val:
            self.visibleLayers.add(layer)
        else:
            self.visibleLayers.discard(layer)
        for cr in self.chunkRenderers.values():
            cr.invalidLayers.add(layer)

        self.loadNearbyChunks()

    def layerProperty(layer, default=True):  # @NoSelf
        attr = sys.intern("_draw" + layer)

        def _get(self):
            return getattr(self, attr, default)

        def _set(self, val):
            if val != _get(self):
                setattr(self, attr, val)
                self.toggleLayer(val, layer)

        return property(_get, _set)

    drawEntities = layerProperty(Layer.Entities)
    drawTileEntities = layerProperty(Layer.TileEntities)
    drawTileTicks = layerProperty(Layer.TileTicks)
    drawMonsters = layerProperty(Layer.Monsters)
    drawItems = layerProperty(Layer.Items)
    drawTerrainPopulated = layerProperty(Layer.TerrainPopulated)

    def inSpace(self):
        if self.level is None:
            return True
        h = self.position[1]
        return ((h > self.level.Height + self.spaceHeight) or
                (h <= -self.spaceHeight))

    def chunkDistance(self, cpos):
        camx, camy, camz = self.position

        # if the renderer is offset into the world somewhere, adjust for that
        ox, oy, oz = self.origin
        camx -= ox
        camz -= oz

        camcx = int(np.floor(camx)) >> 4
        camcz = int(np.floor(camz)) >> 4

        cx, cz = cpos

        return max(abs(cx - camcx), abs(cz - camcz))

    overheadMode = False

    def detailLevelForChunk(self, cpos):
        if self.overheadMode:
            return 2
        if self.isPreviewer:
            w, l, h = self.level.bounds.size
            if w + l < 256:
                return 0

        distance = self.chunkDistance(cpos) - self.viewDistance
        if distance > 0 or self.inSpace():
            return 1
        return 0

    def getViewDistance(self):
        return self._viewDistance

    def setViewDistance(self, vd):
        vd = int(vd) & 0xfffe
        vd = min(max(vd, self.minViewDistance), self.maxViewDistance)
        if vd != self._viewDistance:
            self._viewDistance = vd
            self.viewDistanceChanged()
            # self.invalidateChunkMarkers()

    viewDistance = property(getViewDistance, setViewDistance, None, "View Distance")

    @property
    def effectiveViewDistance(self):
        if self.inSpace():
            return self.viewDistance * 4
        else:
            return self.viewDistance * 2

    def viewDistanceChanged(self):
        self.oldPosition = None  # xxx
        self.discardMasterList()
        self.loadNearbyChunks()
        self.discardChunksOutsideViewDistance()

    maxWorkFactor = 64
    minWorkFactor = 1
    workFactor = 2

    chunkCalculator = None

    _level = None

    @property
    def level(self) -> pymclevel.MCLevel:
        return self._level

    @level.setter
    def level(self, level: pymclevel.MCLevel):
        """ this probably warrants creating a new renderer """
        self.stopWork()

        self._level = level
        self.oldPosition = None
        self.position = (0, 0, 0)
        self.chunkCalculator = None

        self.invalidChunkQueue = deque()

        self.discardAllChunks()

        self.loadableChunkMarkers.invalidate()

        if level:
            self.chunkCalculator = self.calculatorClass(self.level)

            self.oldPosition = None
            level.allChunks

        self.loadNearbyChunks()

    position = (0, 0, 0)

    def loadChunksStartingFrom(self, wx, wz, distance=None):
        """
        Set up self.chunkIterator to load all chunks in the square range around the given block coordinate

        wx: starting x block coordinate to load from

        wz: starting z block coordinate to load from

        distance: The distance in chunks to load from the given (x, z) position, defaults to self.effectiveViewDistance if not provided
        """

        if None is self.level:
            return

        if distance is None:
            d = self.effectiveViewDistance
        else:
            d = distance

        self.chunkIterator = self.iterateChunks(wx, wz, d * 2)

    def iterateChunks(self, x, z, d):
        """
        Builds an iterator for going through all chunks in range of the given coordinate

        x: x block coordinate in the first chunk to load

        z: z block coordinate in the first chunk to load
        
        d: The distance, in number of chunks, to load around the given coordinates
        """

        # Divide the chunk coordinates by 16, i.e. shift 4 bits, to go from block coordinates to chunk coordinates
        cx = int(x) >> 4
        cz = int(z) >> 4

        # First coordinate to iterate
        yield (cx, cz)

        # Start with a 1x1 chunk range, moving forward on the x and x axes
        step = dir = 1

        # Run forever until there's nothing left to iterate
        while True:
            # For the current iteration size, go over the entire x axis for chunks
            for i in range(step):
                cx += dir
                yield (cx, cz)

            # For the current iteration size, go over the entire z axis for chunks
            for i in range(step):
                cz += dir
                yield (cx, cz)

            # Expand the range one chunkout
            step += 1

            # If the max range has been iterated, and in normal chunk loading, nothing left to iterate
            if step > d and not self.overheadMode:
                return

            # Start moving in the opposite direction around the range
            dir = -dir

    chunkIterator = None

    @property
    def chunkWorker(self):
        if self._chunkWorker is None:
            self._chunkWorker = self.makeWorkIterator()
        return self._chunkWorker

    def stopWork(self):
        self._chunkWorker = None

    def discardAllChunks(self):
        self.bufferUsage = 0
        self.forgetAllDisplayLists()
        self.chunkRenderers = {}
        self.oldPosition = None  # xxx force reload

    def discardChunksInBox(self, box):
        self.discardChunks(box.chunkPositions)

    def discardChunksOutsideViewDistance(self):
        if self.overheadMode:
            return

        # print "discardChunksOutsideViewDistance"
        d = self.effectiveViewDistance
        cx = (self.position[0] - self.origin[0]) / 16
        cz = (self.position[2] - self.origin[2]) / 16

        origin = (cx - d, cz - d)
        size = d * 2

        if not len(self.chunkRenderers):
            return
        (ox, oz) = origin
        bytes = 0
        # chunks = np.fromiter(self.chunkRenderers.iterkeys(), dtype='int32', count=len(self.chunkRenderers))
        chunks = np.fromiter(self.chunkRenderers.keys(), dtype='i,i', count=len(self.chunkRenderers))
        chunks.dtype = 'int32'
        chunks.shape = len(self.chunkRenderers), 2

        if size:
            outsideChunks = chunks[:, 0] < ox - 1
            outsideChunks |= chunks[:, 0] > ox + size
            outsideChunks |= chunks[:, 1] < oz - 1
            outsideChunks |= chunks[:, 1] > oz + size
            chunks = chunks[outsideChunks]

        self.discardChunks(chunks)

    def discardChunks(self, chunks):
        for cx, cz in chunks:
            self.discardChunk(cx, cz)
        self.oldPosition = None  # xxx force reload

    def discardChunk(self, cx, cz):
        " discards the chunk renderer for this chunk and compresses the chunk "
        if (cx, cz) in self.chunkRenderers:
            self.bufferUsage -= self.chunkRenderers[cx, cz].bufferSize
            self.chunkRenderers[cx, cz].forgetDisplayLists()
            del self.chunkRenderers[cx, cz]

        self.level.compressChunk(cx, cz)

    _fastLeaves = False

    @property
    def fastLeaves(self):
        return self._fastLeaves

    @fastLeaves.setter
    def fastLeaves(self, val):
        if self._fastLeaves != bool(val):
            self.discardAllChunks()

        self._fastLeaves = bool(val)

    _roughGraphics = False

    @property
    def roughGraphics(self):
        return self._roughGraphics

    @roughGraphics.setter
    def roughGraphics(self, val):
        if self._roughGraphics != bool(val):
            self.discardAllChunks()

        self._roughGraphics = bool(val)

    _showHiddenOres = False

    @property
    def showHiddenOres(self):
        return self._showHiddenOres

    @showHiddenOres.setter
    def showHiddenOres(self, val):
        if self._showHiddenOres != bool(val):
            self.discardAllChunks()

        self._showHiddenOres = bool(val)

    def invalidateChunk(self, cx, cz, layers=None):
        " marks the chunk for regenerating vertex data and display lists "
        if (cx, cz) in self.chunkRenderers:
            # self.chunkRenderers[(cx,cz)].invalidate()
            # self.bufferUsage -= self.chunkRenderers[(cx, cz)].bufferSize

            self.chunkRenderers[(cx, cz)].invalidate(layers)
            # self.bufferUsage += self.chunkRenderers[(cx, cz)].bufferSize

            self.invalidChunkQueue.append((cx, cz))  # xxx encapsulate

    def invalidateChunksInBox(self, box, layers=None):
        box = BoundingBox(box)
        if box.minx & 0xf == 0:
            box.minx -= 1
        if box.miny & 0xf == 0:
            box.miny -= 1
        if box.minz & 0xf == 0:
            box.minz -= 1

        if box.maxx & 0xf == 0:
            box.maxx += 1
        if box.maxy & 0xf == 0:
            box.maxy += 1
        if box.maxz & 0xf == 0:
            box.maxz += 1

        self.invalidateChunks(box.chunkPositions, layers)

    def invalidateEntitiesInBox(self, box):
        self.invalidateChunks(box.chunkPositions, [Layer.Entities])

    def invalidateChunks(self, chunks, layers=None):
        for c in chunks:
            cx, cz = c
            self.invalidateChunk(cx, cz, layers)

        self.stopWork()
        self.discardMasterList()
        self.loadNearbyChunks()

    def invalidateAllChunks(self, layers=None):
        self.invalidateChunks(self.chunkRenderers.keys(), layers)

    def forgetAllDisplayLists(self):
        for cr in self.chunkRenderers.values():
            cr.forgetDisplayLists()

    def invalidateMasterList(self):
        self.discardMasterList()

    shouldRecreateMasterList = True

    def discardMasterList(self):
        self.shouldRecreateMasterList = True

    @property
    def shouldDrawAll(self):
        box = self.level.bounds
        return self.isPreviewer and box.width + box.length < 256

    distanceToChunkReload = 32.0

    def cameraMovedFarEnough(self):
        if self.shouldDrawAll:
            return False
        if self.oldPosition is None:
            return True

        cPos = self.position
        oldPos = self.oldPosition

        cameraDelta = self.distanceToChunkReload

        return any([abs(x - y) > cameraDelta for x, y in zip(cPos, oldPos)])

    def loadVisibleChunks(self):
        """ loads nearby chunks if the camera has moved beyond a certain distance """

        # print "loadVisibleChunks"
        if self.cameraMovedFarEnough():
            if datetime.now() - self.lastVisibleLoad > timedelta(0, 0.5):
                self.discardChunksOutsideViewDistance()
                self.loadNearbyChunks()

                self.oldPosition = self.position
                self.lastVisibleLoad = datetime.now()

    lastVisibleLoad = datetime.now()

    def loadNearbyChunks(self):
        if None is self.level:
            return
        # print "loadNearbyChunks"
        cameraPos = self.position

        if self.shouldDrawAll:
            self.loadAllChunks()
        else:
            # subtract self.origin to load nearby chunks correctly for preview renderers
            self.loadChunksStartingFrom(int(cameraPos[0]) - self.origin[0], int(cameraPos[2]) - self.origin[2])

    def loadAllChunks(self):
        box = self.level.bounds

        self.loadChunksStartingFrom(box.origin[0] + box.width / 2, box.origin[2] + box.length / 2, max(box.width, box.length))

    _floorTexture = None

    @property
    def floorTexture(self):
        if self._floorTexture is None:
            self._floorTexture = Texture(self.makeFloorTex)
        return self._floorTexture

    def makeFloorTex(self):
        color0 = (0xff, 0xff, 0xff, 0x22)
        color1 = (0xff, 0xff, 0xff, 0x44)

        img = np.array([color0, color1, color1, color0], dtype='uint8')

        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 2, 2, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img)

    def invalidateChunkMarkers(self):
        self.loadableChunkMarkers.invalidate()

    def _drawLoadableChunkMarkers(self):
        if self.level.chunkCount:
            chunkSet = set(self.level.allChunks)

            sizedChunks = chunkMarkers(chunkSet)

            GL.glPushAttrib(GL.GL_FOG_BIT)
            GL.glDisable(GL.GL_FOG)

            GL.glEnable(GL.GL_BLEND)
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPolygonOffset(DepthOffset.ChunkMarkers, DepthOffset.ChunkMarkers)
            GL.glEnable(GL.GL_DEPTH_TEST)

            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glColor(1.0, 1.0, 1.0, 1.0)

            self.floorTexture.bind()
            # chunkColor = np.zeros(shape=(chunks.shape[0], 4, 4), dtype='float32')
#            chunkColor[:]= (1, 1, 1, 0.15)
#
#            cc = np.array(chunks[:,0] + chunks[:,1], dtype='int32')
#            cc &= 1
#            coloredChunks = cc > 0
#            chunkColor[coloredChunks] = (1, 1, 1, 0.28)
#            chunkColor *= 255
#            chunkColor = np.array(chunkColor, dtype='uint8')
#
            # GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, 0, chunkColor)
            for size, chunks in sizedChunks.items():
                if not len(chunks):
                    continue
                chunks = np.array(chunks, dtype='float32')

                chunkPosition = np.zeros(shape=(chunks.shape[0], 4, 3), dtype='float32')
                chunkPosition[:, :, (0, 2)] = np.array(((0, 0), (0, 1), (1, 1), (1, 0)), dtype='float32')
                chunkPosition[:, :, (0, 2)] *= size
                chunkPosition[:, :, (0, 2)] += chunks[:, np.newaxis, :]
                chunkPosition *= 16
                GL.glVertexPointer(3, GL.GL_FLOAT, 0, chunkPosition.ravel())
                # chunkPosition *= 8
                GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, (chunkPosition[..., (0, 2)] * 8).ravel())
                GL.glDrawArrays(GL.GL_QUADS, 0, len(chunkPosition) * 4)

            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glDisable(GL.GL_BLEND)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPopAttrib()

    def drawLoadableChunkMarkers(self):
        if not self.isPreviewer or isinstance(self.level, pymclevel.MCBetaLevel):
            self.loadableChunkMarkers.call(self._drawLoadableChunkMarkers)

        # self.drawCompressedChunkMarkers()

    def drawCompressedChunkMarkers(self):
        chunkPositions = list(self.chunkRenderers.keys())
        if 0 == len(chunkPositions):
            return

        chunkPositions = np.array(chunkPositions)

        chunkLoaded = [self.level.chunkIsLoaded(*c) for c in chunkPositions]
        chunkLoaded = np.array(chunkLoaded, dtype='bool')

        chunkCompressed = [self.level.chunkIsCompressed(*c) for c in chunkPositions]
        chunkCompressed = np.array(chunkCompressed, dtype='bool')

        chunkDirty = [self.level.chunkIsDirty(*c) for c in chunkPositions]
        chunkDirty = np.array(chunkDirty, dtype='bool')

        vertexBuffer = np.zeros((len(chunkPositions), 4, 3), dtype='float32')

        vertexBuffer[..., (0, 2)] = np.array(((0, 0), (0, 1), (1, 1), (1, 0)), dtype='float32')

        vertexBuffer[..., (0, 2)] += chunkPositions[:, np.newaxis]
        vertexBuffer[..., (0, 2)] *= 16

        vertexBuffer[..., 1] = 128

        colorBuffer = np.zeros((len(chunkCompressed), 4, 4), dtype='uint8')
        colorBuffer[:] = (0x00, 0x00, 0x00, 0x33)
        colorBuffer[chunkLoaded] = (0xff, 0xff, 0xff, 0x66)
        colorBuffer[chunkCompressed] = (0xff, 0xFF, 0x00, 0x66)
        colorBuffer[chunkDirty] = (0xff, 0x00, 0x00, 0x66)

        cc = np.array(chunkPositions[:, 0] + chunkPositions[:, 1], dtype='int32')
        cc &= 1
        coloredChunks = cc > 0
        colorBuffer[coloredChunks] *= 0.75

        GL.glEnable(GL.GL_BLEND)
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glPolygonOffset(DepthOffset.ChunkMarkers, DepthOffset.ChunkMarkers)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glVertexPointer(3, GL.GL_FLOAT, 0, vertexBuffer)
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, 0, colorBuffer)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(vertexBuffer) * 4)

        GL.glDisableClientState(GL.GL_COLOR_ARRAY)

        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glDisable(GL.GL_BLEND)

    needsImmediateRedraw = False
    viewingFrustum = None
    if "-debuglists" in sys.argv:
        def createMasterLists(self):
            pass

        def callMasterLists(self):
            for cr in self.chunkRenderers.values():
                cr.debugDraw()
    else:
        def createMasterLists(self):
            if self.shouldRecreateMasterList:
                lists = {}
                chunkLists = defaultdict(list)
                chunksPerFrame = 80
                shouldRecreateAgain = False

                for ch in self.chunkRenderers.values():
                    if chunksPerFrame:
                        if ch.needsRedisplay:
                            chunksPerFrame -= 1
                        ch.makeDisplayLists()
                    else:
                        shouldRecreateAgain = True

                    if ch.renderstateLists:
                        for rs in ch.renderstateLists:
                            chunkLists[rs] += ch.renderstateLists[rs]

                for rs in chunkLists:
                    if len(chunkLists[rs]):
                        lists[rs] = np.array(chunkLists[rs], dtype='uint32').ravel()

                # lists = lists[lists.nonzero()]
                self.masterLists = lists
                self.shouldRecreateMasterList = shouldRecreateAgain
                self.needsImmediateRedraw = shouldRecreateAgain

        def callMasterLists(self):
            for renderstate in self.chunkCalculator.renderStates:
                if renderstate not in self.masterLists:
                    continue

                if self.alpha != 0xff and renderstate is not ChunkCalculator.renderStateLowDetail:
                    GL.glEnable(GL.GL_BLEND)
                renderstate.bind()

                GL.glCallLists(self.masterLists[renderstate])

                renderstate.release()
                if self.alpha != 0xff and renderstate is not ChunkCalculator.renderStateLowDetail:
                    GL.glDisable(GL.GL_BLEND)

    errorLimit = 10

    def draw(self):
        self.needsRedraw = False
        if not self.level:
            return
        if not self.chunkCalculator:
            return
        if not self.render:
            return

        chunksDrawn = 0

        with gl.glPushMatrix(GL.GL_MODELVIEW):
            dx, dy, dz = self.origin
            GL.glTranslate(dx, dy, dz)

            GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_DEPTH_TEST)

            self.level.materials.terrainTexture.bind()
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            offset = DepthOffset.PreviewRenderer if self.isPreviewer else DepthOffset.Renderer
            GL.glPolygonOffset(offset, offset)
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

            self.createMasterLists()
            try:
                self.callMasterLists()

            except GL.GLError as e:
                if self.errorLimit:
                    self.errorLimit -= 1
                    traceback.print_exc()
                    print(e)

            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_DEPTH_TEST)

            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
                # if self.drawLighting:
            self.drawLoadableChunkMarkers()

    renderErrorHandled = False

    def addDebugInfo(self, addDebugString):
        addDebugString("BU: {0} MB, ".format(
            self.bufferUsage / 1000000,
             ))

        addDebugString("WQ: {0}, ".format(len(self.invalidChunkQueue)))
        if self.chunkIterator:
            addDebugString("[LR], ")

        addDebugString("CR: {0}, ".format(len(self.chunkRenderers),))

    def __next__(self):
        next(self.chunkWorker)

    def makeWorkIterator(self):
        ''' does chunk face and vertex calculation work. returns a generator that can be
        iterated over for smaller work units.'''

        try:
            while True:
                if self.level is None:
                    return

                if len(self.invalidChunkQueue) > 1024:
                    self.invalidChunkQueue.clear()

                if len(self.invalidChunkQueue):
                    c = self.invalidChunkQueue[0]
                    for i in self.workOnChunk(c):
                        yield
                    self.invalidChunkQueue.popleft()

                elif self.chunkIterator is None:
                    return

                else:
                    try:
                        c = next(self.chunkIterator)
                    except StopIteration:
                        # No more iterations to do, no more work, the iterator is complete
                        return
                    if self.vertexBufferLimit:
                        while self.bufferUsage > (0.9 * (self.vertexBufferLimit << 20)):
                            deadChunk = None
                            deadDistance = self.chunkDistance(c)
                            for cr in self.chunkRenderers.values():
                                dist = self.chunkDistance(cr.chunkPosition)
                                if dist > deadDistance:
                                    deadChunk = cr
                                    deadDistance = dist

                            if deadChunk is not None:
                                self.discardChunk(*deadChunk.chunkPosition)

                            else:
                                break

                        else:
                            for i in self.workOnChunk(c):
                                yield

                    else:
                        for i in self.workOnChunk(c):
                            yield

                yield

        finally:
            self._chunkWorker = None
            if self.chunkIterator:
                self.chunkIterator = None

    vertexBufferLimit = 384

    def getChunkRenderer(self, c):
        if not (c in self.chunkRenderers):
            cr = self.chunkClass(self, c)
        else:
            cr = self.chunkRenderers[c]

        return cr

    def calcFacesForChunkRenderer(self, cr: ChunkRenderer):
        self.bufferUsage -= cr.bufferSize

        calc = cr.calcFaces()
        work = 0
        for i in calc:
            yield
            work += 1

        self.chunkDone(cr, work)

    def workOnChunk(self, c):
        work = 0

        if self.level.containsChunk(*c):
            cr = self.getChunkRenderer(c)
            if self.viewingFrustum:
                # if not self.viewingFrustum.visible(np.array([[c[0] * 16 + 8, 64, c[1] * 16 + 8, 1.0]]), 64).any():
                if not self.viewingFrustum.visible1([c[0] * 16 + 8, self.level.Height / 2, c[1] * 16 + 8, 1.0], self.level.Height / 2):
                    return

            faceInfoCalculator = self.calcFacesForChunkRenderer(cr)
            try:
                for result in faceInfoCalculator:
                    work += 1
                    if (work % MCRenderer.workFactor) == 0:
                        yield

                self.invalidateMasterList()

            except Exception as e:
                traceback.print_exc()
                try:
                    fn = self.level.chunkFilename(*c)
                except Exception:
                    fn = c

                logging.info(u"Skipped chunk {f}: {e}".format(e=e, f=fn))

    redrawChunks = 0

    def chunkDone(self, chunkRenderer, work):
        self.chunkRenderers[chunkRenderer.chunkPosition] = chunkRenderer
        self.bufferUsage += chunkRenderer.bufferSize
        # print "Chunk {0} used {1} work units".format(chunkRenderer.chunkPosition, work)
        if not self.needsRedraw:
            if self.redrawChunks:
                self.redrawChunks -= 1
                if not self.redrawChunks:
                    self.needsRedraw = True

            else:
                self.redrawChunks = 2

        if work > 0:
            self.oldChunkStartTime = self.chunkStartTime
            self.chunkStartTime = datetime.now()
            self.chunkSamples.pop(0)
            self.chunkSamples.append(self.chunkStartTime - self.oldChunkStartTime)

            cx, cz = chunkRenderer.chunkPosition

            for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1), (0, 0)):
                self.tryCompressChunk(cx + dx, cz + dz, (cx, cz))

    def tryCompressChunk(self, cx, cz, donePos):
        neighborChunkPos = [(cx + dx, cz + dz) for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        neighborChunks = [self.chunkRenderers.get(c) for c in neighborChunkPos]
        doneChunks = [cr and cr.done or not self.level.containsChunk(*cPos) or cPos == donePos for cPos, cr in zip(neighborChunkPos, neighborChunks)]

        if all(doneChunks):
            self.level.compressChunk(cx, cz)


class PreviewRenderer(MCRenderer):
    isPreviewer = True

