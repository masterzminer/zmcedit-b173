# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

# Code was copied form SethBing, as stated above, and then modified by masterzminer

from pymclevel import TAG_Short
import log

displayName = "Reset Delay to 0"

def perform(level, box, options):

	for (chunk, slices, point) in level.getChunkSlices(box):
		for e in chunk.TileEntities:
			if e["id"].value == "MobSpawner":
				x = e["x"].value
				y = e["y"].value
				z = e["z"].value
				
				if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
					modify(e, options)
					log.debug(e["EntityId"].value + " spawner at (" + str(x) + ", " + str(y) + ", " + str(z) + ") modified")
					chunk.dirty = True
				
def modify(e, options):
	e["Delay"] = TAG_Short(0)
