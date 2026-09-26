def perform(level, box, options):
    groups = RedstoneGroups(level)
    
    for x in range(box.minx, box.maxx):
        for y in range(box.miny, box.maxy):
            for z in range(box.minz, box.maxz):
                groups.test_block((x, y, z))

    groups.changeBlocks()

    

TransparentBlocks = [0, 6, 8, 9, 10, 11, 18, 20, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 44, 46, 50, 51, 52, 53, 54, 55, 59, 60, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 79, 81, 83, 85, 89, 90, 92, 93, 94, 95, 96, 97, 101, 102, 104, 105, 106, 107, 108, 109, 111, 113, 114, 115, 116, 117, 118, 119, 120, 122, 126, 127]

class RedstoneGroups:
    group = {}
    current_group = 0

    def __init__(self, level):
        self.level = level

    def isRedstone(self, block_id):
        return block_id == 55 or block_id == 93 or block_id == 94

    def test_block(self, pos):
        (x, y, z) = pos
        block_id = self.level.blockAt(x, y, z)
        if self.isRedstone(block_id):
            if (x, y, z) in self.group:
                return
            self.group[pos] = self.current_group
            self.test_neighbors(pos)
            self.current_group = self.current_group + 1

    def test_neighbors(self, position):
        (x, y, z) = position
        for dy in range(-1, 2, 1):
            if y + dy >= 0 and y + dy <= 255:
                self.test_neighbor((x, y, z), (x-1, y+dy, z))
                self.test_neighbor((x, y, z), (x+1, y+dy, z))
                self.test_neighbor((x, y, z), (x, y+dy, z-1))
                self.test_neighbor((x, y, z), (x, y+dy, z+1))

    def test_neighbor(self, pos1, pos2):
        if pos2 in self.group:
            return

        if self.connected(pos1, pos2):
            self.group[pos2] = self.current_group
            self.test_neighbors(pos2)

    def getBlockAt(self, position):
        (x, y, z) = position
        return self.level.blockAt(x, y, z)

    def repeaterAlignedWith(self, pos1, pos2):
        (x1, y1, z1) = pos1
        (x2, y2, z2) = pos2
        block_id = self.getBlockAt((x1, y1, z1))
        if block_id != 93 and block_id != 94:
            return False

        direction = self.level.blockDataAt(x1, y1, z1) % 4

        if (direction == 0 or direction == 2) and abs(z2 - z1) != 1:
            return False
        elif (direction == 1 or direction == 3) and abs(x2 - x1) != 1:
            return False

        return True

    def repeaterPointingTowards(self, pos1, pos2):
        (x1, y1, z1) = pos1
        (x2, y2, z2) = pos2
        block_id = self.getBlockAt((x1, y1, z1))
        if block_id != 93 and block_id != 94:
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

    def repeaterPointingAway(self, pos1, pos2):
        (x1, y1, z1) = pos1
        (x2, y2, z2) = pos2
        block_id = self.getBlockAt((x1, y1, z1))
        if block_id != 93 and block_id != 94:
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
    

    def connected(self, pos1, pos2):
        (x1, y1, z1) = pos1
        (x2, y2, z2) = pos2
        block_id1 = self.level.blockAt(x1, y1, z1)
        block_id2 = self.level.blockAt(x2, y2, z2)

        pos1 = (x1, y1, z1)
        pos2 = (x2, y2, z2)
        
        if y1 == y2:
            if block_id1 == 55:
                if block_id2 == 55:
                    return True
                elif self.repeaterAlignedWith(pos2, pos1):
                    return True                    
            elif self.repeaterAlignedWith(pos1, pos2) and block_id2 == 55:
                return True
            elif self.repeaterPointingTowards(pos1, pos2) and self.repeaterPointingAway(pos2, pos1):
                return True
            elif self.repeaterPointingAway(pos1, pos2) and self.repeaterPointingTowards(pos2, pos1):
                return True
        elif y2 == y1 - 1:
            above_id = self.level.blockAt(x2, y2+1, z2)
            
            if block_id1 == 55:
                if block_id2 == 55 and TransparentBlocks.count(above_id) == 1:
                    return True
                elif self.repeaterAlignedWith(pos2, pos1):
                    return True
            elif self.repeaterPointingTowards(pos1, pos2):
                if block_id2 == 55 and TransparentBlocks.count(above_id) == 0:
                    return True
        elif y2 == y1 + 1:
            return self.connected(pos2, pos1)

        return False

    SkipBlocks = [23, 61, 62, 89]

    def changeBlocks(self):
        for ((x, y, z), gr) in self.group.items():
            if y > 0:
                block_id = self.level.blockAt(x, y-1, z)
                if self.SkipBlocks.count(block_id) == 1:
                    continue
                self.level.setBlockAt(x, y-1, z, 35)
                self.level.setBlockDataAt(x, y-1, z, gr % 16)
                self.level.getChunk(x // 16, z // 16).dirty = True
