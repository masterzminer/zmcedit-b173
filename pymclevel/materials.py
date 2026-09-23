
import numpy as np
import traceback
from os.path import exists, join
from collections import defaultdict
from pprint import pformat

import sys, os

NOTEX = (0xB0, 0xE0)

import yaml

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
        return cmp( key(self), key(other))
        
    hasVariants = False #True if blockData defines additional blocktypes
    def __init__(self, materials, blockID, blockData=0):
        self.materials = materials
        self.ID = blockID
        self.blockData = blockData
        
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        if attr == "name":
            r = self.materials.names[self.ID]
        else:
            r = getattr(self.materials, attr)[self.ID]
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
            
                level.materials[0] #returns Air
                level.materials["Air"] #also returns Air
                level.materials["Powered Rail"] #returns Powered Rail
                level.materials["Lapis Lazuli Block"] #in Classic
                    
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
            bl = Block(self, id, blockData=data)
            bl.hasVariants = True
            return bl
    
    
    
    def addYamlBlocksFromFile(self, filename):
        try:
            from importlib import resources

            f = resources.files(__name__).joinpath(filename).open("rb")
        except (ImportError, IOError):
            root = os.environ.get("PYMCLEVEL_YAML_ROOT", "pymclevel") #fall back to cwd as last resort
            f = open(join(root, filename))
        try:
            info(u"Loading block info from %s", f)
            blockyaml = yaml.safe_load(f)
            self.addYamlBlocks(blockyaml)
 
        except Exception as e:
            print("Exception while loading block info from {f}: {e}")
            traceback.print_exc()
            
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

        block = Block(self, blockID, blockData)
        
        self.allBlocks.append(block)
        self.blocksByType[type].append(block)

        if (blockID, 0) in self.blocksByID:
            self.blocksByID[blockID, 0].hasVariants = True
            block.hasVariants = True

        self.blocksByID[blockID, blockData] = block

        return block

           
                
    
alphaMaterials = MCMaterials(defaultName="Future Block!")
alphaMaterials.name = "Alpha"
alphaMaterials.addYamlBlocksFromFile("minecraft.yaml")





# --- Special treatment for some blocks ---

HugeMushroomTypes = {
   "Northwest" : 1,
   "North" : 2,
   "Northeast" : 3,
   "East" : 6,
   "Southeast" : 9,
   "South" : 8,
   "Southwest" : 7,
   "West" : 4,
   "Stem" : 10,
   "Top" : 5,
}
from .faces import *

Red = (0xD0, 0x70)
Brown = (0xE0, 0x70)
Pore = (0xE0, 0x80)
Stem = (0xD0, 0x80)

def defineShroomFaces(Shroom, id, name):
    for way, data in sorted(list(HugeMushroomTypes.items()), key=lambda a:a[1]):
        loway = way.lower()
        if way == "Stem":
            tex = [Stem, Stem, Pore, Pore, Stem, Stem]
        elif way == "Pore":
            tex = Pore
        else:
            tex = [Pore] * 6
            tex[FaceYIncreasing] = Shroom
            if "north" in loway:
                tex[FaceZDecreasing] = Shroom
            if "south" in loway:
                tex[FaceZIncreasing] = Shroom
            if "west" in loway:
                tex[FaceXDecreasing] = Shroom
            if "east" in loway:
                tex[FaceXIncreasing] = Shroom
                
        alphaMaterials.addBlock(id, blockData = data,
            name="Huge " + name + " Mushroom (" + way + ")",
            texture=tex,
            )

        
defineShroomFaces(Brown, 99, "Brown")
defineShroomFaces(Red, 100, "Red")

classicMaterials = MCMaterials(defaultName = "Not present in Classic")
classicMaterials.name = "Classic"
classicMaterials.addYamlBlocksFromFile("classic.yaml")

# --- Static block defs ---

alphaMaterials.Stone = alphaMaterials[1, 0]
alphaMaterials.Grass = alphaMaterials[2, 0]
alphaMaterials.Dirt = alphaMaterials[3, 0]
alphaMaterials.Cobblestone = alphaMaterials[4, 0]
alphaMaterials.WoodPlanks = alphaMaterials[5, 0]
alphaMaterials.Sapling = alphaMaterials[6, 0]
alphaMaterials.SpruceSapling = alphaMaterials[6, 1]
alphaMaterials.BirchSapling = alphaMaterials[6, 2]
alphaMaterials.Bedrock = alphaMaterials[7, 0]
alphaMaterials.WaterActive = alphaMaterials[8, 0]
alphaMaterials.Water = alphaMaterials[9, 0]
alphaMaterials.LavaActive = alphaMaterials[10, 0]
alphaMaterials.Lava = alphaMaterials[11, 0]
alphaMaterials.Sand = alphaMaterials[12, 0]
alphaMaterials.Gravel = alphaMaterials[13, 0]
alphaMaterials.GoldOre = alphaMaterials[14, 0]
alphaMaterials.IronOre = alphaMaterials[15, 0]
alphaMaterials.CoalOre = alphaMaterials[16, 0]
alphaMaterials.Wood = alphaMaterials[17, 0]
alphaMaterials.Ironwood = alphaMaterials[17, 1]
alphaMaterials.BirchWood = alphaMaterials[17, 2]
alphaMaterials.Leaves = alphaMaterials[18, 0]
alphaMaterials.PineLeaves = alphaMaterials[18, 1]
alphaMaterials.BirchLeaves = alphaMaterials[18, 2]
alphaMaterials.LeavesDecaying = alphaMaterials[18, 4]
alphaMaterials.PineLeavesDecaying = alphaMaterials[18, 5]
alphaMaterials.BirchLeavesDecaying = alphaMaterials[18, 6]
alphaMaterials.Sponge = alphaMaterials[19, 0]
alphaMaterials.Glass = alphaMaterials[20, 0]

alphaMaterials.LapisLazuliOre = alphaMaterials[21, 0]
alphaMaterials.LapisLazuliBlock = alphaMaterials[22, 0]
alphaMaterials.Dispenser = alphaMaterials[23, 0]
alphaMaterials.Sandstone = alphaMaterials[24, 0]
alphaMaterials.NoteBlock = alphaMaterials[25, 0]
alphaMaterials.Bed = alphaMaterials[26, 0]
alphaMaterials.PoweredRail = alphaMaterials[27, 0]
alphaMaterials.DetectorRail = alphaMaterials[28, 0]
alphaMaterials.StickyPiston = alphaMaterials[29, 0]
alphaMaterials.Web = alphaMaterials[30, 0]
alphaMaterials.UnusedShrub = alphaMaterials[31, 0]
alphaMaterials.TallGrass = alphaMaterials[31, 1]
alphaMaterials.Shrub = alphaMaterials[31, 2]
alphaMaterials.DesertShrub2 = alphaMaterials[32, 0]
alphaMaterials.Piston = alphaMaterials[33, 0]
alphaMaterials.PistonHead = alphaMaterials[34, 0]
alphaMaterials.WhiteWool = alphaMaterials[35, 0]
alphaMaterials.OrangeWool = alphaMaterials[35, 1]
alphaMaterials.MagentaWool = alphaMaterials[35, 2]
alphaMaterials.LightBlueWool = alphaMaterials[35, 3]
alphaMaterials.YellowWool = alphaMaterials[35, 4]
alphaMaterials.LightGreenWool = alphaMaterials[35, 5]
alphaMaterials.PinkWool = alphaMaterials[35, 6]
alphaMaterials.GrayWool = alphaMaterials[35, 7]
alphaMaterials.LightGrayWool = alphaMaterials[35, 8]
alphaMaterials.CyanWool = alphaMaterials[35, 9]
alphaMaterials.PurpleWool = alphaMaterials[35, 10]
alphaMaterials.BlueWool = alphaMaterials[35, 11]
alphaMaterials.BrownWool = alphaMaterials[35, 12]
alphaMaterials.DarkGreenWool = alphaMaterials[35, 13]
alphaMaterials.RedWool = alphaMaterials[35, 14]
alphaMaterials.BlackWool = alphaMaterials[35, 15]

alphaMaterials.Flower = alphaMaterials[37, 0]
alphaMaterials.Rose = alphaMaterials[38, 0]
alphaMaterials.BrownMushroom = alphaMaterials[39, 0]
alphaMaterials.RedMushroom = alphaMaterials[40, 0]
alphaMaterials.BlockofGold = alphaMaterials[41, 0]
alphaMaterials.BlockofIron = alphaMaterials[42, 0]
alphaMaterials.DoubleStoneSlab = alphaMaterials[43, 0]
alphaMaterials.DoubleSandstoneSlab = alphaMaterials[43, 1]
alphaMaterials.DoubleWoodenSlab = alphaMaterials[43, 2]
alphaMaterials.DoubleCobblestoneSlab = alphaMaterials[43, 3]
alphaMaterials.DoubleBrickSlab = alphaMaterials[43, 4]
alphaMaterials.DoubleStoneBrickSlab = alphaMaterials[43, 5]
alphaMaterials.StoneSlab = alphaMaterials[44, 0]
alphaMaterials.SandstoneSlab = alphaMaterials[44, 1]
alphaMaterials.WoodenSlab = alphaMaterials[44, 2]
alphaMaterials.CobblestoneSlab = alphaMaterials[44, 3]
alphaMaterials.BrickSlab = alphaMaterials[44, 4]
alphaMaterials.StoneBrickSlab = alphaMaterials[44, 5]
alphaMaterials.Brick = alphaMaterials[45, 0]
alphaMaterials.TNT = alphaMaterials[46, 0]
alphaMaterials.Bookshelf = alphaMaterials[47, 0]
alphaMaterials.MossStone = alphaMaterials[48, 0]
alphaMaterials.Obsidian = alphaMaterials[49, 0]

alphaMaterials.Torch = alphaMaterials[50, 0]
alphaMaterials.Fire = alphaMaterials[51, 0]
alphaMaterials.MonsterSpawner = alphaMaterials[52, 0]
alphaMaterials.WoodenStairs = alphaMaterials[53, 0]
alphaMaterials.Chest = alphaMaterials[54, 0]
alphaMaterials.RedstoneWire = alphaMaterials[55, 0]
alphaMaterials.DiamondOre = alphaMaterials[56, 0]
alphaMaterials.BlockofDiamond = alphaMaterials[57, 0]
alphaMaterials.CraftingTable = alphaMaterials[58, 0]
alphaMaterials.Crops = alphaMaterials[59, 0]
alphaMaterials.Farmland = alphaMaterials[60, 0]
alphaMaterials.Furnace = alphaMaterials[61, 0]
alphaMaterials.LitFurnace = alphaMaterials[62, 0]
alphaMaterials.Sign = alphaMaterials[63, 0]
alphaMaterials.WoodenDoor = alphaMaterials[64, 0]
alphaMaterials.Ladder = alphaMaterials[65, 0]
alphaMaterials.Rail = alphaMaterials[66, 0]
alphaMaterials.StoneStairs = alphaMaterials[67, 0]
alphaMaterials.WallSign = alphaMaterials[68, 0]
alphaMaterials.Lever = alphaMaterials[69, 0]
alphaMaterials.StoneFloorPlate = alphaMaterials[70, 0]
alphaMaterials.IronDoor = alphaMaterials[71, 0]
alphaMaterials.WoodFloorPlate = alphaMaterials[72, 0]
alphaMaterials.RedstoneOre = alphaMaterials[73, 0]
alphaMaterials.RedstoneOreGlowing = alphaMaterials[74, 0]
alphaMaterials.RedstoneTorchOff = alphaMaterials[75, 0]
alphaMaterials.RedstoneTorchOn = alphaMaterials[76, 0]
alphaMaterials.Button = alphaMaterials[77, 0]
alphaMaterials.SnowLayer = alphaMaterials[78, 0]
alphaMaterials.Ice = alphaMaterials[79, 0]
alphaMaterials.Snow = alphaMaterials[80, 0]

alphaMaterials.Cactus = alphaMaterials[81, 0]
alphaMaterials.Clay = alphaMaterials[82, 0]
alphaMaterials.SugarCane = alphaMaterials[83, 0]
alphaMaterials.Jukebox = alphaMaterials[84, 0]
alphaMaterials.Fence = alphaMaterials[85, 0]
alphaMaterials.Pumpkin = alphaMaterials[86, 0]
alphaMaterials.Netherrack = alphaMaterials[87, 0]
alphaMaterials.SoulSand = alphaMaterials[88, 0]
alphaMaterials.Glowstone = alphaMaterials[89, 0]
alphaMaterials.NetherPortal = alphaMaterials[90, 0]
alphaMaterials.JackOLantern = alphaMaterials[91, 0]
alphaMaterials.Cake = alphaMaterials[92, 0]
alphaMaterials.RedstoneRepeaterOff = alphaMaterials[93, 0]
alphaMaterials.RedstoneRepeaterOn = alphaMaterials[94, 0]
alphaMaterials.AprilFoolsChest = alphaMaterials[95, 0]
alphaMaterials.Trapdoor = alphaMaterials[96, 0]

alphaMaterials.HiddenSilverfishStone = alphaMaterials[97, 0]
alphaMaterials.HiddenSilverfishCobblestone = alphaMaterials[97, 1]
alphaMaterials.HiddenSilverfishStoneBrick = alphaMaterials[97, 2]
alphaMaterials.StoneBricks = alphaMaterials[98, 0]
alphaMaterials.MossyStoneBricks = alphaMaterials[98, 1]
alphaMaterials.CrackedStoneBricks = alphaMaterials[98, 2]
alphaMaterials.HugeBrownMushroom = alphaMaterials[99, 0]
alphaMaterials.HugeRedMushroom = alphaMaterials[100, 0]
alphaMaterials.IronBars = alphaMaterials[101, 0]
alphaMaterials.GlassPane = alphaMaterials[102, 0]
alphaMaterials.Watermelon = alphaMaterials[103, 0]
alphaMaterials.PumpkinStem = alphaMaterials[104, 0]
alphaMaterials.MelonStem = alphaMaterials[105, 0]
alphaMaterials.Vines = alphaMaterials[106, 0]
alphaMaterials.FenceGate = alphaMaterials[107, 0]
alphaMaterials.BrickStairs = alphaMaterials[108, 0]
alphaMaterials.StoneBrickStairs = alphaMaterials[109, 0]
alphaMaterials.Mycelium = alphaMaterials[110, 0]
alphaMaterials.Lilypad = alphaMaterials[111, 0]
alphaMaterials.NetherBrick = alphaMaterials[112, 0]
alphaMaterials.NetherBrickFence = alphaMaterials[113, 0]
alphaMaterials.NetherBrickStairs = alphaMaterials[114, 0]
alphaMaterials.NetherWart = alphaMaterials[115, 0]

# --- Classic static block defs ---
classicMaterials.Stone = classicMaterials[1]
classicMaterials.Grass = classicMaterials[2]
classicMaterials.Dirt = classicMaterials[3]
classicMaterials.Cobblestone = classicMaterials[4]
classicMaterials.WoodPlanks = classicMaterials[5]
classicMaterials.Sapling = classicMaterials[6]
classicMaterials.Bedrock = classicMaterials[7]
classicMaterials.WaterActive = classicMaterials[8]
classicMaterials.Water = classicMaterials[9]
classicMaterials.LavaActive = classicMaterials[10]
classicMaterials.Lava = classicMaterials[11]
classicMaterials.Sand = classicMaterials[12]
classicMaterials.Gravel = classicMaterials[13]
classicMaterials.GoldOre = classicMaterials[14]
classicMaterials.IronOre = classicMaterials[15]
classicMaterials.CoalOre = classicMaterials[16]
classicMaterials.Wood = classicMaterials[17]
classicMaterials.Leaves = classicMaterials[18]
classicMaterials.Sponge = classicMaterials[19]
classicMaterials.Glass = classicMaterials[20]

classicMaterials.RedWool = classicMaterials[21] 
classicMaterials.OrangeWool = classicMaterials[22] 
classicMaterials.YellowWool = classicMaterials[23] 
classicMaterials.LimeWool = classicMaterials[24] 
classicMaterials.GreenWool = classicMaterials[25] 
classicMaterials.AquaWool = classicMaterials[26] 
classicMaterials.CyanWool = classicMaterials[27] 
classicMaterials.BlueWool = classicMaterials[28] 
classicMaterials.PurpleWool = classicMaterials[29] 
classicMaterials.IndigoWool = classicMaterials[30]
classicMaterials.VioletWool = classicMaterials[31] 
classicMaterials.MagentaWool = classicMaterials[32] 
classicMaterials.PinkWool = classicMaterials[33] 
classicMaterials.BlackWool = classicMaterials[34] 
classicMaterials.GrayWool = classicMaterials[35] 
classicMaterials.WhiteWool = classicMaterials[36] 

classicMaterials.Flower = classicMaterials[37]
classicMaterials.Rose = classicMaterials[38]
classicMaterials.BrownMushroom = classicMaterials[39]
classicMaterials.RedMushroom = classicMaterials[40]
classicMaterials.BlockofGold = classicMaterials[41]
classicMaterials.BlockofIron = classicMaterials[42]
classicMaterials.DoubleStoneSlab = classicMaterials[43]
classicMaterials.StoneSlab = classicMaterials[44]
classicMaterials.Brick = classicMaterials[45]
classicMaterials.TNT = classicMaterials[46]
classicMaterials.Bookshelf = classicMaterials[47]
classicMaterials.MossStone = classicMaterials[48]
classicMaterials.Obsidian = classicMaterials[49]


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

allMaterials = (alphaMaterials, classicMaterials)

_conversionFuncs = {}
def conversionFunc(destMats, sourceMats):
    if destMats is sourceMats: return nullConversion
    func = _conversionFuncs.get((destMats, sourceMats))
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
    _conversionFuncs[(destMats, sourceMats)] = func
    return func

def convertBlocks(destMats, sourceMats, blocks, blockData):
    if sourceMats == destMats: return blocks, blockData
    
    return conversionFunc(destMats, sourceMats)(blocks, blockData)
    
namedMaterials = dict((i.name, i) for i in allMaterials)

__all__ = "alphaMaterials, classicMaterials, namedMaterials, MCMaterials".split(", ")
