# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from __future__ import absolute_import
from __future__ import print_function
from pymclevel import TAG_Long

# This mimics some of the functionality from the Java Random class.
# Java Random source code can be found here: http://developer.classpath.org/doc/java/util/Random-source.html
class Random:
	def __init__(self, randseed):
		self.setSeed(randseed)

	def setSeed(self, randseed):
		self.randseed = (randseed ^ 0x5DEECE66D) & ((1 << 48) - 1);
		
	def next(self, bits):
		self.randseed = int(self.randseed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
		return int(self.randseed >> (48 - bits))

	def nextInt(self, n):
		while True:
			bits = self.next(31)
			val = bits % n
			if int(bits - val + (n-1)) >= 0:
				break
			
		return val

# Algorithm found here: http://www.minecraftforum.net/topic/397835-find-slime-spawning-chunks-125/
def slimeChunk(seed, x, z):
	randseed = int(seed) + int(x * x * 0x4c1906) + int(x * 0x5ac0db) + int(z * z) * 0x4307a7 + int(z * 0x5f24f) ^ 0x3ad8025f
	r = Random(randseed)
	i = r.nextInt(10)
	return i == 0
	
def goodSeed(box, seed):
	minx = int(box.minx/16)*16
	minz = int(box.minz/16)*16

	for x in range(minx, box.maxx, 16):
		for z in range(minz, box.maxz, 16):
			if slimeChunk(seed, x, z):
				return False
				
	
	return True

inputs = (
	("Max Seed", 100000),
)

def perform(level, box, options):
	for seed in range(options["Max Seed"]):
		if goodSeed(box, int(seed)):
			level.root_tag["Data"]["RandomSeed"] = TAG_Long(seed)
			print("Found good seed: " + str(seed))
			return
	
	print("Didn't find good seed.")