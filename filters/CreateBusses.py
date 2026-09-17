# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from __future__ import absolute_import
from numpy import sign

displayName = "Create Busses"

def perform(level, box, options):
	level.markDirtyBox(box)
	
	bus = BusCreator(level, box, options)
	bus.getTerminals()
	bus.getGuides()
	bus.pickAllPaths()
	bus.createAllBusses()
	
HorizDirs = [
	(1, 0, 0),
	(-1, 0, 0),
	(0, 0, 1),
	(0, 0, -1),
	]

Down = (0, -1, 0)
Up = (0, 1, 0)

def getHorizDir(xxx_todo_changeme9, xxx_todo_changeme10):
	(x1, y1, z1) = xxx_todo_changeme9
	(x2, y2, z2) = xxx_todo_changeme10
	if abs(x2-x1) > abs(z2-z1):
		return (sign(x2-x1), 0, 0)
	else:
		if(z2 == z1):
			return (1, 0, 0)
		else:
			return (0, 0, sign(z2-z1))

def getSecondaryDir(xxx_todo_changeme11, xxx_todo_changeme12):
	(x1, y1, z1) = xxx_todo_changeme11
	(x2, y2, z2) = xxx_todo_changeme12
	if abs(x2-x1) > abs(z2-z1):
		return (0, 0, sign(z2-z1))
	else:
		return (sign(x2-x1), 0, 0)
		
def leftOf(xxx_todo_changeme13, xxx_todo_changeme14):
	(dx1, dy1, dz1) = xxx_todo_changeme13
	(dx2, dy2, dz2) = xxx_todo_changeme14
	return dx1 == dz2 or dz1 == dx2 * -1

def rotateRight(xxx_todo_changeme15):
	(dx, dy, dz) = xxx_todo_changeme15
	return ((-dz, dy, dx))

def rotateLeft(xxx_todo_changeme16):
	(dx, dy, dz) = xxx_todo_changeme16
	return ((dz, dy, -dx))

def allAdjacentSamePlane(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			dir,
			left,
			right,
			getDir(dir, Up),
			getDir(dir, Down),
			getDir(left, Up),
			getDir(right, Up),
			getDir(left, Down),
			getDir(right, Down),
			back,
			getDir(back, Up),
			getDir(back, Down),
			)
	else:
		return (
			dir,
			right,
			left,
			getDir(dir, Up),
			getDir(dir, Down),
			getDir(right, Up),
			getDir(left, Up),
			getDir(right, Down),
			getDir(left, Down),
			back,
			getDir(back, Up),
			getDir(back, Down),
			)

def allAdjacentUp(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			getDir(dir, Up),
			getDir(left, Up),
			getDir(right, Up),
			getDir(back, Up),
			dir,
			left,
			right,
			back,
			getDir(dir, Down),
			getDir(left, Down),
			getDir(right, Down),
			getDir(back, Down),
			)
	else:
		return (
			getDir(dir, Up),
			getDir(right, Up),
			getDir(left, Up),
			getDir(back, Up),
			dir,
			right,
			left,
			back,
			getDir(dir, Down),
			getDir(right, Down),
			getDir(left, Down),
			getDir(back, Down),
			)
		
def allAdjacentDown(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			getDir(dir, Down),
			getDir(left, Down),
			getDir(right, Down),
			getDir(back, Down),
			dir,
			left,
			right,
			back,
			getDir(dir, Up),
			getDir(left, Up),
			getDir(right, Up),
			getDir(back, Up),
			)
	else:
		return (
			getDir(dir, Down),
			getDir(right, Down),
			getDir(left, Down),
			getDir(back, Down),
			dir,
			right,
			left,
			back,
			getDir(dir, Up),
			getDir(right, Up),
			getDir(left, Up),
			getDir(back, Up),
			)
		
def getDir(xxx_todo_changeme17, xxx_todo_changeme18):
	(x, y, z) = xxx_todo_changeme17
	(dx, dy, dz) = xxx_todo_changeme18
	return (x+dx, y+dy, z+dz)

def dist(xxx_todo_changeme19, xxx_todo_changeme20):
	(x1, y1, z1) = xxx_todo_changeme19
	(x2, y2, z2) = xxx_todo_changeme20
	return abs(x2-x1) + abs(y2-y1) + abs(z2-z1)
	
def above(xxx_todo_changeme21, xxx_todo_changeme22):
	(x1, y1, z1) = xxx_todo_changeme21
	(x2, y2, z2) = xxx_todo_changeme22
	return y1 > y2

def below(xxx_todo_changeme23, xxx_todo_changeme24):
	(x1, y1, z1) = xxx_todo_changeme23
	(x2, y2, z2) = xxx_todo_changeme24
	return y1 < y2
	
def insideBox(box, xxx_todo_changeme25):
	(x, y, z) = xxx_todo_changeme25
	return x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz

Colors = {
	0: "white",
	1: "orange",
	2: "magenta",
	3: "light blue",
	4: "yellow",
	5: "lime green",
	6: "pink",
	7: "gray",
	8: "light gray",
	9: "cyan",
	10:"purple",
	11:"blue",
	12:"brown",
	13:"green",
	14:"red",
	15:"black",
	}
	
class BusCreator:
	starts = {}
	ends = {}
	guides = {}
	path = {}

	
	def __init__(self, level, box, options):
		self.level = level
		self.box = box
		self.options = options
	
	def getTerminals(self):
		for x in range(self.box.minx, self.box.maxx):
			for y in range(self.box.miny, self.box.maxy):
				for z in range(self.box.minz, self.box.maxz):
					(color, start) = self.isTerminal((x, y, z))
					if color != None and start != None:
						if start:
							if color in self.starts:
								raise Exception("Duplicate starting point for " + Colors[color] + " bus")
							self.starts[color] = (x, y, z)
						else:
							if color in self.ends:
								raise Exception("Duplicate ending point for " + Colors[color] + " bus")
							self.ends[color] = (x, y, z)
							
	def getGuides(self):
		for x in range(self.box.minx, self.box.maxx):
			for y in range(self.box.miny, self.box.maxy):
				for z in range(self.box.minz, self.box.maxz):
					pos = (x, y, z)
					if self.getBlockAt(pos) == 35:
						color = self.getBlockDataAt(pos)
						
						if color not in self.starts or color not in self.ends:
							continue
						
						if color not in self.guides:
							self.guides[color] = []
						
						rs = getDir(pos, Up)
						if rs == self.starts[color] or rs == self.ends[color]:
							continue
						
						self.guides[color].append(rs)
					
	
	def isTerminal(self, xxx_todo_changeme):
		(x, y, z) = xxx_todo_changeme
		pos = (x, y, z)
		for dir in HorizDirs:
			otherPos = getDir(pos, dir)
			
			towards = self.repeaterPointingTowards(pos, otherPos)
			away = self.repeaterPointingAway(pos, otherPos)
			if not (away or towards): # it's not a repeater pointing towards or away
				continue
			if self.getBlockAt(otherPos) != 55: # the other block isn't redstone
				continue
			if self.getBlockAt(getDir(pos, Down)) != 35: # it's not sitting on wool
				continue
			if self.getBlockAt(getDir(otherPos, Down)) != 35: # the other block isn't sitting on wool
				continue
			
			data = self.getBlockDataAt(getDir(pos, Down))
			if self.getBlockDataAt(getDir(otherPos, Down)) != data: # the wool colors don't match
				continue
			
			return (data, towards)
		
		return (None, None)
	
	def pickAllPaths(self):
		for color in range(0, 16):
			if color in self.starts and color in self.ends:
				self.pickPath(color)
	
	def pickPath(self, color):
		self.path[color] = ()
		currentPos = self.starts[color]
		
		while True:
			minDist = None
			minGuide = None
			for guide in self.guides[color]:
				guideDist = dist(currentPos, guide)
				if minDist == None or guideDist < minDist:
					minDist = guideDist
					minGuide = guide
			
			if dist(currentPos, self.ends[color]) == 1:
				return
				
			if minGuide == None:
				return
			
			self.path[color] = self.path[color] + (minGuide,)
			currentPos = minGuide
			self.guides[color].remove(minGuide)

	def createAllBusses(self):
		for color in range(0, 16):
			if color in self.path:
				self.connectDots(color)			
			
	def connectDots(self, color):
		prevGuide = None
		self.power = 1
		for guide in self.path[color]:
			if prevGuide != None:
				self.createConnection(prevGuide, guide, color)
			
			prevGuide = guide
			
			
	def createConnection(self, pos1, pos2, color):
		currentPos = pos1
	
		while currentPos != pos2:
			self.power = self.power + 1
			
			hdir = getHorizDir(currentPos, pos2)
			secondaryDir = getSecondaryDir(currentPos, pos2)

			if above(currentPos, pos2):
				dirs = allAdjacentDown(hdir, secondaryDir)
			elif below(currentPos, pos2):
				dirs = allAdjacentUp(hdir, secondaryDir)
			else:
				dirs = allAdjacentSamePlane(hdir, secondaryDir)
				
			if self.power == 1:
				restrictions = 2
			elif self.power == 15:
				restrictions = 1
			else:
				restrictions = 0
			
			placed = False
			for dir in dirs:
				pos = getDir(currentPos, dir)
				if self.canPlaceRedstone(pos, currentPos, pos2, restrictions):
					if self.power == 15:
						self.placeRepeater(pos, dir, color)
						self.power = 0
					else:
						self.placeRedstone(pos, color)
					currentPos = pos
					placed = True
					break
			
			if not placed:
				#raise Exception("Algorithm failed to create bus for " + Colors[color] + " wire.")
				return
					
			
	
	def canPlaceRedstone(self, pos, fromPos, destinationPos, restrictions):
		if restrictions == 1 and above(pos, fromPos): #repeater
			return False
		
		if restrictions == 2 and below(pos, fromPos): #just after repeater
			return False
		
		if restrictions == 2 and not self.repeaterPointingTowards(fromPos, pos): #just after repeater
			return False
	
		if above(pos, fromPos) and self.getBlockAt(getDir(getDir(pos, Down), Down)) == 55:
			return False
		
		if below(pos, fromPos) and self.getBlockAt(getDir(pos, Up)) != 0:
			return False
		
		if getDir(pos, Down) == destinationPos:
			return False
		
		if pos == destinationPos:
			return True
			
		if self.getBlockAt(pos) != 0:
			return False
		
		if self.getBlockAt(getDir(pos, Down)) != 0:
			return False
		
		if not insideBox(self.box, pos):
			return False
	
		for dir in allAdjacentSamePlane((1, 0, 0), (0, 0, 0)):
			testPos = getDir(pos, dir)
			if testPos == fromPos or testPos == getDir(fromPos, Down):
				continue
			
			if testPos == destinationPos or testPos == getDir(destinationPos, Down):
				continue

			blockid = self.getBlockAt(testPos)
			if blockid != 0:
				return False
		
		return True
			
	
	def placeRedstone(self, pos, color):
		self.setBlockAt(pos, 55) #redstone
		self.setBlockAt(getDir(pos, Down), 35, color) # wool
		
	def placeRepeater(self, pos, xxx_todo_changeme1, color):
		(dx, dy, dz) = xxx_todo_changeme1
		if dz == -1:
			self.setBlockAt(pos, 93, 0) #north
		elif dx == 1:
			self.setBlockAt(pos, 93, 1) #east
		elif dz == 1:
			self.setBlockAt(pos, 93, 2) #south
		elif dx == -1:
			self.setBlockAt(pos, 93, 3) #west
			
		self.setBlockAt(getDir(pos, Down), 35, color) #wool
		
	def getBlockAt(self, xxx_todo_changeme2):
		(x, y, z) = xxx_todo_changeme2
		return self.level.blockAt(x, y, z)
		
	def getBlockDataAt(self, xxx_todo_changeme3):
		(x, y, z) = xxx_todo_changeme3
		return self.level.blockDataAt(x, y, z)
		
	def setBlockAt(self, xxx_todo_changeme4, id, dmg = 0):
		(x, y, z) = xxx_todo_changeme4
		self.level.setBlockAt(x, y, z, id)
		self.level.setBlockDataAt(x, y, z, dmg)
				
	def repeaterPointingTowards(self, xxx_todo_changeme5, xxx_todo_changeme6):
		(x1, y1, z1) = xxx_todo_changeme5
		(x2, y2, z2) = xxx_todo_changeme6
		blockid = self.getBlockAt((x1, y1, z1))
		if blockid != 93 and blockid != 94:
			return False

		direction = self.level.blockDataAt(x1, y1, z1) % 4

		if direction == 0 and z2 - z1 == -1:
			return True
		if direction == 1 and x2 - x1 == 1:
			return True
		if direction == 2 and z2 - z1 == 1:
			return True
		if direction == 3 and x2 - x1 == -1:
			return True

		return False

	def repeaterPointingAway(self, xxx_todo_changeme7, xxx_todo_changeme8):
		(x1, y1, z1) = xxx_todo_changeme7
		(x2, y2, z2) = xxx_todo_changeme8
		blockid = self.getBlockAt((x1, y1, z1))
		if blockid != 93 and blockid != 94:
			return False

		direction = self.level.blockDataAt(x1, y1, z1) % 4

		if direction == 0 and z2 - z1 == 1:
			return True
		if direction == 1 and x2 - x1 == -1:
			return True
		if direction == 2 and z2 - z1 == -1:
			return True
		if direction == 3 and x2 - x1 == 1:
			return True

		return False
		