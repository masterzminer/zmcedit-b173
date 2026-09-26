

from numpy import zeros
import itertools
from pymclevel import alphaMaterials
from pymclevel.level import extractHeights

am = alphaMaterials

#naturally occurring materials
blocks = [
  am.Grass,
  am.Dirt,
  am.Stone,
  am.Bedrock,
  am.Sand,
  am.Gravel,
  am.GoldOre,
  am.IronOre,
  am.CoalOre,
  am.LapisLazuliOre,
  am.DiamondOre,
  am.RedstoneOre,
  am.RedstoneOreGlowing,
  am.Netherrack,
  am.SoulSand,
  am.Clay,
  am.Glowstone
]
block_types = [b.ID for b in blocks]


def naturalBlockMask():
    block_mask = zeros((256,), dtype='bool')
    block_mask[block_types] = True
    return block_mask

inputs = (
  ("Depth", (4, -128, 128)),
  ("Pick a block:", alphaMaterials.Grass),
)


def perform(level, box, options):
    depth = options["Depth"]
    blocktype = options["Pick a block:"]

    #compute a truth table that we can index to find out whether a block
    # is naturally occuring and should be considered in a height map
    block_mask = naturalBlockMask()

    # always consider the chosen blocktype to be "naturally occurring" to stop
    # it from adding extra layers
    block_mask[blocktype.ID] = True

    #iterate through the slices of each chunk in the selection box
    for chunk, slices, point in level.getChunkSlices(box):
        # slicing the block array is straightforward. blocks will contain only
        # the area of interest in this chunk.
        blocks = chunk.Blocks[slices]
        data = chunk.Data[slices]

        # use indexing to look up whether or not each block in blocks is
        # naturally-occurring. these blocks will "count" for column height.
        maskedBlocks = block_mask[blocks]

        height_map = extractHeights(maskedBlocks)

        for x, z in itertools.product(*list(map(range, height_map.shape))):
            h = height_map[x, z]
            if depth > 0:
                blocks[x, z, max(0, h - depth):h] = blocktype.ID
                data[x, z, max(0, h - depth):h] = blocktype.blockData
            else:
                #negative depth values mean to put a layer above the surface
                blocks[x, z, h:min(blocks.shape[2], h - depth)] = blocktype.ID
                data[x, z, h:min(blocks.shape[2], h - depth)] = blocktype.blockData

        #remember to do this to make sure the chunk is saved
        chunk.chunkChanged()
