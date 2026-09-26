"""
DeCliff filter contributed by Minecraft Forums user "DrRomz"

Originally posted here:
http://www.minecraftforum.net/topic/13807-mcedit-minecraft-world-editor-compatible-with-mc-beta-18/page__st__3940__p__7648793#entry7648793
"""

import numpy as np
import itertools
from pymclevel import alphaMaterials
am = alphaMaterials

# Consider below materials when determining terrain height
blocks = [
  am.Stone,
  am.Grass,
  am.Dirt,
  am.Bedrock,
  am.Sand,
  am.Sandstone,
  am.Clay,
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
  am.Glowstone
]
terrainBlockTypes = [b.ID for b in blocks]
terrainBlockMask = np.zeros((256,), dtype='bool')

# Truth table used to calculate terrain height
# trees, leaves, etc. sit on top of terrain
terrainBlockMask[terrainBlockTypes] = True

inputs = (
    # Option to limit change to raise_cliff_floor / lower_cliff_top
    # Default is to adjust both and meet somewhere in the middle
    ("Raise/Lower", ("Both", "Lower Only", "Raise Only")),
)


#
# Calculate the maximum adjustment that can be made from
# cliff_pos in direction dir (-1/1) keeping terrain at most
# max step blocks away from previous column
def max_adj(height_map, slice_no, cliff_pos, dir, pushup, max_step, slice_width):
    ret = 0
    if dir < 0:
        if cliff_pos < 2:
            return 0
        end = 0
    else:
        if cliff_pos > slice_width - 2:
            return 0
        end = slice_width - 1

    for cur_pos in range(cliff_pos, end, dir):
        if pushup:
            ret = ret + \
               max([0, max_step - dir * height_map[slice_no, cur_pos] + \
               dir * height_map[slice_no, cur_pos + dir]])
        else:
            ret = ret + \
               min([0, -max_step + dir * height_map[slice_no, cur_pos] - \
               dir * height_map[slice_no, cur_pos + dir]])

    return ret


#
# Raise/lower column at cliff face by adj and decrement change as we move away
# from the face. Each level will be at most max_step blocks from those beside it.
#
# This function doesn't actually change anything, but just sets array 'new'
# with the desired height.
def adj_height(orig, new, slice_no, cliff_pos, dir, adj, can_adj, max_step, slice_width):
    cur_adj = adj
    prev = 0
    done_adj = 0

    if dir < 0:
        end = 1
    else:
        end = slice_width - 1

    if adj == 0 or can_adj == 0:
        for cur_pos in range(cliff_pos, end, dir):
            new[slice_no, cur_pos] = orig[slice_no, cur_pos]
    else:

        for cur_pos in range(cliff_pos, end, dir):
            if adj > 0:
                done_adj = done_adj + \
                           max([0, max_step - orig[slice_no, cur_pos] + \
                           orig[slice_no, cur_pos + dir]])

                if orig[slice_no, cur_pos] - \
                    orig[slice_no, cur_pos + dir] > 0:
                    cur_adj = max([0, cur_adj - orig[slice_no, cur_pos] + \
                            orig[slice_no, cur_pos + dir]])
                    prev = adj - cur_adj
            else:
                done_adj = done_adj + \
                           min([0, -max_step + \
                               orig[slice_no, cur_pos] - \
                               orig[slice_no, cur_pos + dir]])
                if orig[slice_no, cur_pos] - \
                   orig[slice_no, cur_pos + dir] > 0:
                    cur_adj = min([0, cur_adj + orig[slice_no, cur_pos] - orig[slice_no, cur_pos + dir]])
                    prev = adj - cur_adj
            new[slice_no, cur_pos] = max([0, orig[slice_no, cur_pos] + cur_adj])
            if cur_adj != 0 and \
               abs(prev) < abs(int(adj * done_adj / can_adj)):
                cur_adj = cur_adj + (prev - int(adj * done_adj / can_adj))
                prev = int(adj * done_adj / can_adj)

    new[slice_no, end] = orig[slice_no, end]


def perform(level, box, options):
    if box.volume > 16000000:
        raise ValueError("Volume too big for this filter method!")

    RLOption = options["Raise/Lower"]
    schema = level.extractSchematic(box)
    schema.removeEntitiesInBox(schema.bounds)
    schema.removeTileEntitiesInBox(schema.bounds)

    terrainBlocks = terrainBlockMask[schema.Blocks]

    coords = terrainBlocks.nonzero()

    # Swap values around so long edge of selected rectangle is first
    # - the long edge is assumed to run parallel to the cliff face
    #   and we want to process slices perpendicular to the face
    #  height map will have x,z (or z,x) index with highest ground level
    if schema.Width > schema.Length:
        height_map = np.zeros((schema.Width, schema.Length), dtype='float32')
        height_map[coords[0], coords[1]] = coords[2]
        newHeightMap = np.zeros((schema.Width, schema.Length), dtype='uint16')
        slice_count = schema.Width
        slice_width = schema.Length
    else:
        height_map = np.zeros((schema.Length, schema.Width), dtype='float32')
        height_map[coords[1], coords[0]] = coords[2]
        newHeightMap = np.zeros((schema.Length, schema.Width), dtype='uint16')
        slice_count = schema.Length
        slice_width = schema.Width

    nonTerrainBlocks = ~terrainBlocks
    nonTerrainBlocks &= schema.Blocks != 0

    for slice_no in range(0, slice_count):

        cliff_height = 0
        # determine pos and height of cliff in this slice
        for cur_pos in range(0, slice_width - 1):
            if abs(height_map[slice_no, cur_pos] - height_map[slice_no, cur_pos + 1]) > abs(cliff_height):
                cliff_height = height_map[slice_no, cur_pos] - height_map[slice_no, cur_pos + 1]
                cliff_pos = cur_pos

        if abs(cliff_height) < 2:
            # nothing to adjust - just copy height map to new hight map
            adj_height(height_map, newHeightMap, slice_no, 0, 1, 0, 1, 1, slice_width)
            continue

        # Try to keep adjusted columns within 1 column of their neighbors
        # but ramp up to 4 blocks up/down on each column when needed
        for max_step in range(1, 4):

            can_left = max_adj(height_map, slice_no, cliff_pos, -1, cliff_height < 0, max_step, slice_width)
            can_right = max_adj(height_map, slice_no, cliff_pos + 1, 1, cliff_height > 0, max_step, slice_width)

            if can_right < 0 and RLOption == "Raise Only":
                can_right = 0
            if can_right > 0 and RLOption == "Lower Only":
                can_right = 0
            if can_left < 0 and RLOption == "Raise Only":
                can_left = 0
            if can_left > 0 and RLOption == "Lower Only":
                can_left = 0

            if cliff_height < 0 and can_right - can_left < cliff_height:
                if abs(can_left) > abs(can_right):
                    adj_left = -1 * (cliff_height - max([int(cliff_height / 2), can_right]))
                    adj_right = cliff_height + adj_left
                else:
                    adj_right = cliff_height - max([int(cliff_height / 2), -can_left])
                    adj_left = -1 * (cliff_height - adj_right + 1)
            else:
                if cliff_height > 0 and can_right - can_left > cliff_height:
                    if abs(can_left) > abs(can_right):
                        adj_left = -1 * (cliff_height - min([int(cliff_height / 2), can_right]))
                        adj_right = cliff_height + adj_left
                    else:
                        adj_right = cliff_height - min([int(cliff_height / 2), -can_left]) - 1
                        adj_left = -1 * (cliff_height - adj_right)
                else:
                    adj_right = 0
                    adj_left = 0
                    continue
            break

        adj_height(height_map, newHeightMap, slice_no, cliff_pos, -1, adj_left, can_left, max_step, slice_width)
        adj_height(height_map, newHeightMap, slice_no, cliff_pos + 1, 1, adj_right, can_right, max_step, slice_width)

    # OK, newHeightMap has new height for each column
    # so it's just a matter of moving everything up/down
    for x, z in itertools.product(range(1, schema.Width - 1), range(1, schema.Length - 1)):

        if schema.Width > schema.Length:
            oh = height_map[x, z]
            nh = newHeightMap[x, z]
        else:
            oh = height_map[z, x]
            nh = newHeightMap[z, x]

        oh = int(oh)
        nh = int(nh)

        delta = nh - oh

        column = np.array(schema.Blocks[x, z])
        # Keep bottom 5 blocks, so we don't lose bedrock
        keep = min([5, nh])

        water_depth = 0
        # Detect Water on top
        if column[oh + 1:oh + 2] == am.Water.ID or column[oh + 1:oh + 2] == am.Ice.ID:
            for cur_pos in range(oh + 1, schema.Height):
                if column[cur_pos:cur_pos + 1] != am.Water.ID and column[cur_pos:cur_pos + 1] != am.Ice.ID: break
                water_depth = water_depth + 1

        if delta == 0:
            column[oh:] = schema.Blocks[x, z, oh:]

        if delta < 0:
            # Moving column down
            column[keep:delta] = schema.Blocks[x, z, keep - delta:]
            column[delta:] = am.Air.ID
            if water_depth > 0:
                # Avoid steeping small lakes, etc on cliff top
                # replace with dirt 'n grass
                column[nh:nh + 1] = am.Grass.ID
                column[nh + 1:nh + 1 + delta] = am.Air.ID
        if delta > 0:
            # Moving column up
            column[keep + delta:] = schema.Blocks[x, z, keep:-delta]
            # Put stone in gap at the bottom
            column[keep:keep + delta] = am.Stone.ID

            if water_depth > 0:
                if water_depth > delta:
                    # Retain Ice
                    if column[nh + water_depth:nh + water_depth + 1] == am.Ice.ID:
                        column[nh + water_depth - delta:nh + 1 + water_depth - delta] = \
                            am.Ice.ID
                    column[nh + 1 + water_depth - delta:nh + 1 + water_depth] = am.Air.ID
                else:
                    if water_depth < delta - 2:
                        column[nh:nh + 1] = am.Grass.ID
                        column[nh + 1:nh + 1 + water_depth] = am.Air.ID
                    else:
                        # Beach at the edge
                        column[nh - 4:nh - 2] = am.Sandstone.ID
                        column[nh - 2:nh + 1] = am.Sand.ID
                        column[nh + 1:nh + 1 + water_depth] = am.Air.ID

        schema.Blocks[x, z] = column

    level.copyBlocksFrom(schema, schema.bounds, box.origin)
