from pymclevel.material import materials
import numpy as np

displayName = "Random Blocks"

inputs = (
	("Replace Rate", (16, 1, 999999999)),
    ("Find", materials.Stone),
    ("Replace With", materials.Cobblestone),
)

def perform(level, box, options):
    # Unpack options
    replace_rate = options["Replace Rate"]
    replace_freq = 1.0 / replace_rate
    keep_freq = 1 - replace_freq
    find_block = options["Find"]
    replace_block = options["Replace With"]

    # Go through all of the portions of chunks that are in the level and in the filter box
    # Note that this approach is substantially faster than going through every index of the box one by one,
    # as it allows numpy to efficiently access the underlying arrays, rather than slow python loops
    for chunk, slices, point in level.getChunkSlices(box):
        # Get the blocks and block data from the current chunk slice
        blocks = chunk.Blocks[slices]
        data = chunk.Data[slices]
        
        # Create a mask based on random chance
        mask = np.random.choice([False, True], blocks.shape, p=[keep_freq, replace_freq])

        # Only replace the block being replaced
        mask[(blocks != find_block.ID) | (data != find_block.blockData)] = False

        # Replace the actual blocks using the mask to determine which blocks to replace
        blocks[mask] = replace_block.ID
        data[mask] = replace_block.blockData

        # Indicate that the chunk has been changed
        chunk.chunkChanged()