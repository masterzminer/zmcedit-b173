
import numpy as np
import itertools
from pymclevel.level import extractHeights

terrainBlocktypes = [1, 2, 3, 7, 12, 13, 14, 15, 16, 56, 73, 74, 87, 88, 89]
terrain_block_mask = np.zeros((256,), dtype='bool')
terrain_block_mask[terrainBlocktypes] = True

#
inputs = (
    ("Repeat count", (1, 50)),
)


def perform(level, box, options):
    repeatCount = options["Repeat count"]
    schematic = level.extractSchematic(box)
    schematic.removeEntitiesInBox(schematic.bounds)
    schematic.removeTileEntitiesInBox(schematic.bounds)

    for _ in range(repeatCount):

        terrainBlocks = terrain_block_mask[schematic.Blocks]

        heightmap = extractHeights(terrainBlocks)

        nonTerrainBlocks = ~terrainBlocks
        nonTerrainBlocks &= schematic.Blocks != 0

        newHeightmap = (heightmap[1:-1, 1:-1] + (heightmap[0:-2, 1:-1] + heightmap[2:, 1:-1] + heightmap[1:-1, 0:-2] + heightmap[1:-1, 2:]) * 0.7) / 3.8
        newHeightmap += 0.5
        newHeightmap[newHeightmap < 0] = 0
        newHeightmap[newHeightmap > schematic.Height] = schematic.Height

        newHeightmap = np.array(newHeightmap, dtype='uint16')

        for x, z in itertools.product(range(1, schematic.Width - 1), range(1, schematic.Length - 1)):
            oh = heightmap[x, z]
            nh = newHeightmap[x - 1, z - 1]
            d = int(nh - oh)

            column = np.array(schematic.Blocks[x, z])
            column[nonTerrainBlocks[x, z]] = 0

            if nh > oh:

                column[d:] = schematic.Blocks[x, z, :-d]
                if d > oh:
                    column[:d] = schematic.Blocks[x, z, 0]
            if nh < oh:
                column[:d] = schematic.Blocks[x, z, -d:]
                column[d:oh + 1] = schematic.Blocks[x, z, min(oh + 1, schematic.Height - 1)]

            # Preserve non-terrain blocks
            column[~terrain_block_mask[column]] = 0
            column[nonTerrainBlocks[x, z]] = schematic.Blocks[x, z][nonTerrainBlocks[x, z]]

            schematic.Blocks[x, z] = column

    level.copyBlocksFrom(schematic, schematic.bounds, box.origin)
