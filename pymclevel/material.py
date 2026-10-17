
import numpy as np
import traceback
from collections import defaultdict
from pprint import pformat

NOTEX = (0xB0, 0xE0)

import yaml
import directories

import logging
log = logging.getLogger(__file__)
debug, info, warn, error, critical = log.debug, log.info, log.warn, log.error, log.critical


class Block(object):
    """
    Value object representing an (id, data) pair.
    Provides elements of its parent material's block arrays.
    Blocks will have (name, ID, blockData, aka, color, brightness, opacity, blockTextures)
    """
    
    def __str__(self):
        return "<Block {name} ({id}:{data}) hasVariants:{ha}>".format(
            name=self.name, id=self.ID, data=self.blockData, ha=self.hasVariants)

    def __repr__(self):
        return str(self)
    
    def __cmp__(self, other):
        if not isinstance(other, Block): return -1
        key = lambda a:a and (a.ID, a.blockData)
        return np.cmp( key(self), key(other))
        
    hasVariants = False #True if blockData defines additional blocktypes
    def __init__(self, blockID, blockData=0):
        self.ID = blockID
        self.blockData = blockData
        
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        if attr == "name":
            r = materials.names[self.ID]
        else:
            r = getattr(materials, attr)[self.ID]
        if attr in ("name", "aka", "color", "type"):
            r = r[self.blockData]
        return r
            
        
class MCMaterials(object):
    defaultColor = (0xc9, 0x77, 0xf0, 0xff)
    defaultBrightness = 0
    defaultOpacity = 15
    defaultTexture = NOTEX
    defaultTex = [t//16 for t in defaultTexture]
    
    def __init__(self, defaultName="Unused Block"):
        object.__init__(self)
        self.yamlDatas = []
        
        self.defaultName = defaultName

        self.blockTextures = np.zeros((256, 16, 6, 2), dtype='uint8')
        self.blockTextures[:] = self.defaultTexture
        self.names = [[defaultName] * 16 for i in range(256)]
        self.aka = [[""] * 16 for i in range(256)]
        
        self.type = [["NORMAL"] * 16] * 256
        self.blocksByType = defaultdict(list)
        self.allBlocks = []
        self.blocksByID = {}

        self.lightEmission = np.zeros(256, dtype='uint8')
        self.lightEmission[:] = self.defaultBrightness
        self.lightAbsorption = np.zeros(256, dtype='uint8')
        self.lightAbsorption[:] = self.defaultOpacity
        self.flatColors = np.zeros((256, 16, 4), dtype='uint8')
        self.flatColors[:] = self.defaultColor
        
        self.idStr = {}
        
        self.color = self.flatColors
        self.brightness = self.lightEmission
        self.opacity = self.lightAbsorption
        
        self.Air = self.addBlock(0,
            name="Air",
            texture=(0x80, 0xB0),
            opacity=0,
        )  
    def __repr__(self):
        return "<MCMaterials ({0})>".format(self.name)
    
    @property
    def AllStairs(self):
        return [b for b in self.allBlocks if b.name.endswith("Stairs")]

    def get(self, key, default = None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __len__(self):
        return len(self.allBlocks)
        
    def __iter__(self):
        return iter(self.allBlocks) 
        
    def __getitem__(self, key):
        """ Let's be magic. If we get a string, return the first block whose 
            name matches exactly. If we get a (id, data) pair or an id, return
            that block. for example:
            
                materials[0] #returns Air
                materials["Air"] #also returns Air
                materials["Powered Rail"] #returns Powered Rail
                materials["Lapis Lazuli Block"] #in Classic
                    
           """
        if isinstance(key, str):
            for b in self.allBlocks:
                if b.name == key: return b
            raise KeyError("No blocks named: " + key)
        if isinstance(key, (tuple, list)):
            id, blockData = key
            return self.blockWithID(id, blockData)
        return self.blockWithID(key)
            
    def blocksMatching(self, name):
        name = name.lower()
        return [v for v in self.allBlocks if name in v.name.lower() or name in v.aka.lower()]

    def blockWithID(self, id, data=0):
        if (id, data) in self.blocksByID:
            return self.blocksByID[id, data]
        else:
            bl = Block(id, blockData=data)
            bl.hasVariants = True
            return bl
    
    
    
    def addYamlBlocksFromFile(self, filename):
        with open(filename) as f:
            info("Loading block info from %s", f)
            block_yaml = yaml.safe_load(f)
            self.addYamlBlocks(block_yaml)
            
    def addYamlBlocks(self, blockyaml):
        self.yamlDatas.append(blockyaml)
        for block in blockyaml['blocks']:
            try:
                self.addYamlBlock(block)
            except Exception as e:
                warn(u"Exception while parsing block: %s", e)
                traceback.print_exc()
                warn(u"Block definition: \n%s", pformat(block))
                    
            
    
    def addYamlBlock(self, kw):
        blockID = kw['id']
        
        unused_yaml_properties = \
        ['explored',
         #'id',
         #'idStr',
         #'mapcolor',
         #'name',
         #'tex',
         ###'tex_data',
         #'tex_direction',
         ###'tex_direction_data',
         'tex_extra',
         #'type'
         ]
        
        for val, data in kw.get('data', {0:{}}).items():
            datakw = dict(kw)
            datakw.update(data)
            idStr = datakw.get('idStr', "")
            tex = [t*16 for t in datakw.get('tex', self.defaultTex)]
            texture = [tex] * 6
            texDirs = {
                "FORWARD":5,
                "BACKWARD":4,
                "LEFT":1,
                "RIGHT":0,
                "TOP":2,
                "BOTTOM":3,
            }
            for dirname, dirtex in datakw.get('tex_direction', {}).items():
                if dirname == "SIDES":
                    for dirname in ("LEFT", "RIGHT"):
                        texture[texDirs[dirname]] = [t*16 for t in dirtex]
                if dirname in texDirs:
                    texture[texDirs[dirname]] = [t*16 for t in dirtex]
            datakw['texture'] = texture
            #print datakw
            block = self.addBlock(blockID, val, **datakw)
            block.yaml = datakw
            if idStr not in self.idStr:
                self.idStr[idStr] = block
            
        tex_direction_data = kw.get('tex_direction_data')
        if tex_direction_data:
            texture = datakw['texture']
            #X+0, X-1, Y+, Y-, Z+b, Z-f
            texDirMap = {
                "NORTH": 0,
                "EAST": 1,
                "SOUTH": 2,
                "WEST": 3,
            }
            def rot90cw():
                rot = (5, 0, 2, 3, 4, 1)
                texture[:] = [texture[r] for r in rot]
            
            for data, dir in tex_direction_data.items():
                for _i in range(texDirMap.get(dir, 0)):
                    rot90cw()
                self.blockTextures[blockID][data] = texture
                
    def addBlock(self, blockID, blockData=0, **kw):
        name = kw.pop('name', self.names[blockID][blockData])
        
        self.lightEmission[blockID] = kw.pop('brightness', self.defaultBrightness)
        self.lightAbsorption[blockID] = kw.pop('opacity', self.defaultOpacity)
        self.aka[blockID][blockData] = kw.pop('aka', "")
        type = kw.pop('type', 'NORMAL')
        
        color = kw.pop('mapcolor', self.flatColors[blockID, blockData])
        self.flatColors[blockID, (blockData or slice(None))] = (tuple(color) + (255,))[:4]

        texture = kw.pop('texture', None)
        
        if texture:
            self.blockTextures[blockID, (blockData or slice(None))] = texture

        if blockData == 0:
            self.names[blockID] = [name] * 16
            self.type[blockID] = [type] * 16
        else:
            self.names[blockID][blockData] = name
            self.type[blockID][blockData] = type

        block = Block(blockID, blockData)
        
        self.allBlocks.append(block)
        self.blocksByType[type].append(block)

        if (blockID, 0) in self.blocksByID:
            self.blocksByID[blockID, 0].hasVariants = True
            block.hasVariants = True

        self.blocksByID[blockID, blockData] = block

        return block

           
                
    
materials = MCMaterials(defaultName="Unknown")
materials.addYamlBlocksFromFile(directories.ASSETS / "minecraft.yaml")


from .faces import *

# --- Static block defs ---

materials.Stone = materials[1, 0]
materials.Grass = materials[2, 0]
materials.Dirt = materials[3, 0]
materials.Cobblestone = materials[4, 0]
materials.WoodPlanks = materials[5, 0]
materials.Sapling = materials[6, 0]
materials.SpruceSapling = materials[6, 1]
materials.BirchSapling = materials[6, 2]
materials.Bedrock = materials[7, 0]
materials.WaterActive = materials[8, 0]
materials.Water = materials[9, 0]
materials.LavaActive = materials[10, 0]
materials.Lava = materials[11, 0]
materials.Sand = materials[12, 0]
materials.Gravel = materials[13, 0]
materials.GoldOre = materials[14, 0]
materials.IronOre = materials[15, 0]
materials.CoalOre = materials[16, 0]
materials.Wood = materials[17, 0]
materials.Ironwood = materials[17, 1]
materials.BirchWood = materials[17, 2]
materials.Leaves = materials[18, 0]
materials.PineLeaves = materials[18, 1]
materials.BirchLeaves = materials[18, 2]
materials.LeavesDecaying = materials[18, 4]
materials.PineLeavesDecaying = materials[18, 5]
materials.BirchLeavesDecaying = materials[18, 6]
materials.Sponge = materials[19, 0]
materials.Glass = materials[20, 0]

materials.LapisLazuliOre = materials[21, 0]
materials.LapisLazuliBlock = materials[22, 0]
materials.Dispenser = materials[23, 0]
materials.Sandstone = materials[24, 0]
materials.NoteBlock = materials[25, 0]
materials.Bed = materials[26, 0]
materials.PoweredRail = materials[27, 0]
materials.DetectorRail = materials[28, 0]
materials.StickyPiston = materials[29, 0]
materials.Web = materials[30, 0]
materials.UnusedShrub = materials[31, 0]
materials.TallGrass = materials[31, 1]
materials.Shrub = materials[31, 2]
materials.DesertShrub2 = materials[32, 0]
materials.Piston = materials[33, 0]
materials.PistonHead = materials[34, 0]
materials.WhiteWool = materials[35, 0]
materials.OrangeWool = materials[35, 1]
materials.MagentaWool = materials[35, 2]
materials.LightBlueWool = materials[35, 3]
materials.YellowWool = materials[35, 4]
materials.LightGreenWool = materials[35, 5]
materials.PinkWool = materials[35, 6]
materials.GrayWool = materials[35, 7]
materials.LightGrayWool = materials[35, 8]
materials.CyanWool = materials[35, 9]
materials.PurpleWool = materials[35, 10]
materials.BlueWool = materials[35, 11]
materials.BrownWool = materials[35, 12]
materials.DarkGreenWool = materials[35, 13]
materials.RedWool = materials[35, 14]
materials.BlackWool = materials[35, 15]

materials.Flower = materials[37, 0]
materials.Rose = materials[38, 0]
materials.BrownMushroom = materials[39, 0]
materials.RedMushroom = materials[40, 0]
materials.BlockofGold = materials[41, 0]
materials.BlockofIron = materials[42, 0]
materials.DoubleStoneSlab = materials[43, 0]
materials.DoubleSandstoneSlab = materials[43, 1]
materials.DoubleWoodenSlab = materials[43, 2]
materials.DoubleCobblestoneSlab = materials[43, 3]
materials.DoubleBrickSlab = materials[43, 4]
materials.StoneSlab = materials[44, 0]
materials.SandstoneSlab = materials[44, 1]
materials.WoodenSlab = materials[44, 2]
materials.CobblestoneSlab = materials[44, 3]
materials.BrickSlab = materials[44, 4]
materials.Brick = materials[45, 0]
materials.TNT = materials[46, 0]
materials.Bookshelf = materials[47, 0]
materials.MossStone = materials[48, 0]
materials.Obsidian = materials[49, 0]

materials.Torch = materials[50, 0]
materials.Fire = materials[51, 0]
materials.MonsterSpawner = materials[52, 0]
materials.WoodenStairs = materials[53, 0]
materials.Chest = materials[54, 0]
materials.RedstoneWire = materials[55, 0]
materials.DiamondOre = materials[56, 0]
materials.BlockofDiamond = materials[57, 0]
materials.CraftingTable = materials[58, 0]
materials.Crops = materials[59, 0]
materials.Farmland = materials[60, 0]
materials.Furnace = materials[61, 0]
materials.LitFurnace = materials[62, 0]
materials.Sign = materials[63, 0]
materials.WoodenDoor = materials[64, 0]
materials.Ladder = materials[65, 0]
materials.Rail = materials[66, 0]
materials.StoneStairs = materials[67, 0]
materials.WallSign = materials[68, 0]
materials.Lever = materials[69, 0]
materials.StoneFloorPlate = materials[70, 0]
materials.IronDoor = materials[71, 0]
materials.WoodFloorPlate = materials[72, 0]
materials.RedstoneOre = materials[73, 0]
materials.RedstoneOreGlowing = materials[74, 0]
materials.RedstoneTorchOff = materials[75, 0]
materials.RedstoneTorchOn = materials[76, 0]
materials.Button = materials[77, 0]
materials.SnowLayer = materials[78, 0]
materials.Ice = materials[79, 0]
materials.Snow = materials[80, 0]

materials.Cactus = materials[81, 0]
materials.Clay = materials[82, 0]
materials.SugarCane = materials[83, 0]
materials.Jukebox = materials[84, 0]
materials.Fence = materials[85, 0]
materials.Pumpkin = materials[86, 0]
materials.Netherrack = materials[87, 0]
materials.SoulSand = materials[88, 0]
materials.Glowstone = materials[89, 0]
materials.NetherPortal = materials[90, 0]
materials.JackOLantern = materials[91, 0]
materials.Cake = materials[92, 0]
materials.RedstoneRepeaterOff = materials[93, 0]
materials.RedstoneRepeaterOn = materials[94, 0]
materials.AprilFoolsChest = materials[95, 0]
materials.Trapdoor = materials[96, 0]


_indices = np.rollaxis(np.indices( (256, 16) ), 0, 3)

def _filterTable(filters, unavailable, default = (0, 0) ):
    #a filter table is a 256x16 table of (ID, data) pairs.
    table = np.zeros((256, 16, 2), dtype='uint8')
    table[:] = _indices
    for u in unavailable:
        try:
            if u[1] == 0:
                u = u[0]
        except TypeError:
            pass
        table[u] = default
    for f, t in filters:
        try:
            if f[1] == 0:
                f = f[0]
        except TypeError:
            pass
        table[f] = t
    return table    
    
nullConversion = lambda b, d: (b, d)

def filterConversion(table):
    def convert(blocks, data):
        if data is None:
            data = 0
        t = table[blocks, data]
        return t[..., 0], t[..., 1]
    return convert
    

def guessFilterTable(matsFrom, matsTo):
    """ Returns a pair (filters, unavailable)
    filters is a list of (from, to) pairs;  from and to are (ID, data) pairs
    unavailable is a list of (ID, data) pairs in matsFrom not found in matsTo.
    
    Searches the 'name' and 'aka' fields to find matches.
    """
    filters = []
    unavailable = []
    toByName = dict(((b.name, b) for b in sorted(matsTo.allBlocks, reverse=True)))
    for fromBlock in matsFrom.allBlocks:
        block = toByName.get(fromBlock.name)
        if block is None:
            for b in matsTo.allBlocks:
                if b.name.startswith(fromBlock.name):
                    block = b
                    break
        if block is None:
            for b in matsTo.allBlocks:
                if fromBlock.name in b.name:
                    block = b
                    break
        if block is None:
            for b in matsTo.allBlocks:
                if fromBlock.name in b.aka:
                    block = b
                    break
        if block is None:
            if "Indigo Wool" == fromBlock.name:
                block = toByName.get("Purple Wool")
            elif "Violet Wool" == fromBlock.name:
                block = toByName.get("Purple Wool")
                
        if block:
            if block != fromBlock:
                filters.append( ( (fromBlock.ID, fromBlock.blockData), (block.ID, block.blockData) ) )
        else:
            unavailable.append((fromBlock.ID, fromBlock.blockData) )
            
    return filters , unavailable

_conversionFunctions = {}
def conversionFunc(destMats, sourceMats):
    if destMats is sourceMats: return nullConversion
    func = _conversionFunctions.get((destMats, sourceMats))
    if func: return func
        
    filters, unavailable = guessFilterTable(sourceMats, destMats)
    debug("")
    debug("%s %s %s", sourceMats.name, "=>", destMats.name)
    for a,b in [(sourceMats.blockWithID(*a), destMats.blockWithID(*b)) for a,b in filters]:
        debug("{0:20}: \"{1}\"".format('"' + a.name + '"',b.name))
    
    debug("")
    debug("Missing blocks: %s", [sourceMats.blockWithID(*a).name for a in unavailable])
    
    table = _filterTable(filters, unavailable, (35, 0))
    func = filterConversion(table)
    _conversionFunctions[(destMats, sourceMats)] = func
    return func

def convertBlocks(destMats, sourceMats, blocks, blockData):
    if sourceMats == destMats: return blocks, blockData
    
    return conversionFunc(destMats, sourceMats)(blocks, blockData)
    