# SethBling's SetBiome Filter
# Directions: Just select a region and use this filter, it will apply the
# biome to all columns within the selected region. It can be used on regions
# of any size, they need not correspond to chunks.
#
# If you modify and redistribute this code, please credit SethBling

inputs = (
    ("Biome", ("Desert",
               "Ocean",
               "Plains",
               "Mountains",
               "Forest",
               "Taiga",
               "Swamp",
               "River",
               "Nether",
               "Frozen Ocean",
               "Frozen River",
               "Ice Plains",
               "Ice Mountains",
               "Beach",
               "Desert Hills",
               "Forest Hills",
               "Taiga Hills",
               "Mountains Edge",
               )),
)

biomes = {
    "Ocean":0,
    "Plains":1,
    "Desert":2,
    "Mountains":3,
    "Forest":4,
    "Taiga":5,
    "Swamp":6,
    "River":7,
    "Nether":8,
    "Frozen Ocean":10,
    "Frozen River":11,
    "Ice Plains":12,
    "Ice Mountains":13,
    "Beach":16,
    "Desert Hills":17,
    "Forest Hills":18,
    "Taiga Hills":19,
    "Mountains Edge":20,
    }

def perform(level, box, options):
    biome = biomes[options["Biome"]]

    minx = int(box.minx/16)*16
    minz = int(box.minz/16)*16

    for x in range(minx, box.maxx, 16):
        for z in range(minz, box.maxz, 16):
            chunk = level.getChunk(x / 16, z / 16)
            chunk.decompress()
            chunk.dirty = True
            array = chunk.root_tag["Level"]["Biomes"].value

            chunkx = int(x/16)*16
            chunkz = int(z/16)*16

            for bx in range(max(box.minx, chunkx), min(box.maxx, chunkx+16)):
                for bz in range(max(box.minz, chunkz), min(box.maxz, chunkz+16)):
                    idx = 16*(bz-chunkz)+(bx-chunkx)
                    array[idx] = biome

            chunk.root_tag["Level"]["Biomes"].value = array
