# Version 5
'''This takes a base MineCraft level and adds or edits trees.
Place it in the folder where the save files are (usually .../.minecraft/saves)
Requires mcInterface.py in the same folder.'''

# Here are the variables you can edit.

# This is the name of the map to edit.
# Make a backup if you are experimenting!


LOADNAME = "LevelSave"

# How many trees do you want to add?
TREE_COUNT = 12

# Where do you want the new trees?
# X, and Z are the map coordinates
X = 66
Z = -315
# How large an area do you want the trees to be in?
# for example, RADIUS = 10 will make place trees randomly in
# a circular area 20 blocks wide.
RADIUS = 80
# NOTE: tree density will be higher in the center than at the edges.

# Which shapes would you like the trees to be?
# these first three are best suited for small heights, from 5 - 10
# "normal" is the normal minecraft shape, it only gets taller and shorter
# "bamboo" a trunk with foliage, it only gets taller and shorter
# "palm" a trunk with a fan at the top, only gets taller and shorter
# "stickly" selects randomly from "normal", "bamboo" and "palm"
# these last five are best suited for very large trees, heights greater than 8
# "round" procedural spherical shaped tree, can scale up to immense size
# "cone" procedural, like a pine tree, also can scale up to immense size
# "procedural" selects randomly from "round" and "conical"
# "rainforest" many slender trees, most at the lower range of the height,
# with a few at the upper end.
# "mangrove" makes mangrove trees (see PLANT_ON below).
SHAPE = "procedural"

# What height should the trees be?
# Specifies the average height of the tree
# Examples:
# 5 is normal minecraft tree
# 3 is minecraft tree with foliage flush with the ground
# 10 is very tall trees, they will be hard to chop down
# NOTE: for round and conical, this affects the foliage size as well.

# CENTER_HEIGHT is the height of the trees at the center of the area
# ie, when radius = 0
CENTER_HEIGHT = 55

# EDGE_HEIGHT is the height at the trees at the edge of the area.
# ie, when radius = RADIUS
EDGE_HEIGHT = 25

# What should the variation in HEIGHT be?
# actual value +- variation
# default is 1
# Example:
# HEIGHT = 8 and HEIGHT_VARIATION = 3 will result in
# trunk heights from 5 to 11
# value is clipped to a max of HEIGHT
# for a good rainforest, set this value not more than 1/2 of HEIGHT
HEIGHT_VARIATION = 12

# Do you want branches, trunk, and roots?
# True makes all of that
# False does not create the trunk and branches, or the roots (even if they are
# enabled further down)
WOOD = True

# Trunk thickness multiplyer
# from zero (super thin trunk) to whatever huge number you can think of.
# Only works if SHAPE is not a "stickly" subtype
# Example:
# 1.0 is the default, it makes decently normal sized trunks
# 0.3 makes very thin trunks
# 4.0 makes a thick trunk (good for HOLLOW_TRUNK).
# 10.5 will make a huge thick trunk.  Not even kidding. Makes spacious
# hollow trunks though!
TRUNK_THICKNESS = 1.0

# Trunk height, as a fraction of the tree
# Only works on "round" shaped trees
# Sets the height of the crown, where the trunk ends and splits
# Examples:
# 0.7 the default value, a bit more than half of the height
# 0.3 good for a fan-like tree
# 1.0 the trunk will extend to the top of the tree, and there will be no crown
# 2.0 the trunk will extend out the top of the foliage, making the tree appear
# like a cluster of green grapes impaled on a spike.
TRUNK_HEIGHT = 0.7

# Do you want the trunk and tree broken off at the top?
# removes about half of the top of the trunk, and any foliage
# and branches that would attach above it.
# Only works if SHAPE is not a "stickly" subtype
# This results in trees that are shorter than the height settings
# True does that stuff
# False makes a normal tree (default)
BROKEN_TRUNK = False
# Note, this works well with HOLLOW_TRUNK (below) turned on as well.

# Do you want the trunk to be hollow (or filled) inside?
# Only works with larger sized trunks.
# Only works if SHAPE is not a "stickly" subtype
# True makes the trunk hollow (or filled with other stuff)
# False makes a solid trunk (default)
HOLLOW_TRUNK = False
# Note, this works well with BROKEN_TRUNK set to true (above)
# Further note, you may want to use a large value for TRUNK_THICKNESS

# How many branches should there be?
# General multiplyer for the number of branches
# However, it will not make more branches than foliage clusters
# so to guarantee a branch to every foliage cluster, set it very high, like 10000
# this also affects the number of roots, if they are enabled.
# Examples:
# 1.0 is normal
# 0.5 will make half as many branches
# 2.0 will make twice as many branches
# 10000 will make a branch to every foliage cluster (I'm pretty sure)
BRANCH_DENSITY = 1.0

# do you want roots from the bottom of the tree?
# Only works if SHAPE is "round" or "cone" or "procedural"
# "yes" roots will penetrate anything, and may enter underground caves.
# "to_stone" roots will be stopped by stone (default see STOPS_ROOTS below).
#    There may be some penetration.
# "hanging" will hang downward in air.  Good for "floating" type maps
#    (I really miss "floating" terrain as a default option)
# "no" roots will not be generated
ROOTS = "to_stone"

# Do you want root buttresses?
# These make the trunk not-round at the base, seen in tropical or old trees.
# This option generally makes the trunk larger.
# Only works if SHAPE is "round" or "cone" or "procedural"
# Options:
# True makes root buttresses
# False leaves them out
ROOT_BUTTRESSES = True

# Do you want leaves on the trees?
# True there will be leaves
# False there will be no leaves
FOLIAGE = True

# How thick should the foliage be
# General multiplyer for the number of foliage clusters
# Examples:
# 1.0 is normal
# 0.3 will make very sparse spotty trees, half as many foliage clusters
# 2.0 will make dense foliage, better for the "rain forests" SHAPE
FOLIAGE_DENSITY = 1.0

# Limit the tree height to the top of the map?
# True the trees will not grow any higher than the top of the map
# False the trees may be cut off by the top of the map
MAP_HEIGHT_LIMIT = True

# add lights in the middle of foliage clusters
# for those huge trees that get so dark underneath
# or for enchanted forests that should glow and stuff
# Only works if SHAPE is "round" or "cone" or "procedural"
# 0 makes just normal trees
# 1 adds one light inside the foliage clusters for a bit of light
# 2 adds two lights around the base of each cluster, for more light
# 4 adds lights all around the base of each cluster for lots of light
LIGHT_TREE = 0

# Do you want to only place trees near existing trees?
# True will only plant new trees near existing trees.
# False will not check for existing trees before planting.
# NOTE: the taller the tree, the larger the forest needs to be to qualify
# OTHER NOTE: this feature has not been extensively tested.
# IF YOU HAVE PROBLEMS: SET TO False
ONLY_IN_FORESTS = False

#####################
# Advanced options! #
#####################

# What kind of material should the "wood" be made of?
# defaults to 17
WOOD_MAT = 17

# What data value should the wood blocks have?
# Some blocks, like wood, leaves, and cloth change
# appearance with different data values
# defaults to 0
WOOD_DATA = 0

# What kind of material should the "leaves" be made of?
# defaults to 18
LEAF_MAT = 18

# What data value should the leaf blocks have?
# Some blocks, like wood, leaves, and cloth change
# appearance with different data values
# defaults to 0
LEAF_DATA = 0

# What kind of material should the "lights" be made of?
# defaults to 89 (glowstone)
LIGHT_MAT = 89

# What data value should the light blocks have?
# defaults to 0
LIGHT_DATA = 0

# What kind of material would you like the "hollow" trunk filled with?
# defaults to 0 (air)
TRUNK_FILL_MAT = 0

# What data value would you like the "hollow" trunk filled with?
# defaults to 0
TRUNK_FILL_DATA = 0

# What kind of blocks should the trees be planted on?
# Use the Minecraft index.
# Examples
# 2 is grass (the default)
# 3 is dirt
# 1 is stone (an odd choice)
# 12 is sand (for beach or desert)
# 9 is water (if you want an aquatic forest)
# this is a list, and comma seperated.
# example: [2, 3]
# will plant trees on grass or dirt
PLANT_ON = [2]

# What kind of blocks should stop the roots?
# a list of block id numbers like PLANT_ON
# Only works if ROOTS = "to_stone"
# default, [1] (stone)
# if you want it to be stopped by other block types, add it to the list
STOPS_ROOTS = [1]

# What kind of blocks should stop branches?
# same as STOPS_ROOTS above, but is always turned on
# defaults to stone, cobblestone, and glass
# set it to [] if you want branches to go through everything
STOPS_BRANCHES = [1, 4, 20]

# How do you want to interpolate from center to edge?
# "linear" makes a cone-shaped forest
# This is the only option at present
INTERPOLATION = "linear"

# Do a rough recalculation of the lighting?
# Slows it down to do a very rough and incomplete re-light.
# If you want to really fix the lighting, use a seperate re-lighting tool.
# True  do the rough fix
# False don't bother
LIGHTING_FIX = True

# How many times do you want to try to find a location?
# it will stop planing after MAX_TRIES has been exceeded.
# Set to smaller numbers to abort quicker, or larger numbers
# if you want to keep trying for a while.
# NOTE: the number of trees will not exceed this number
# Default: 1000
MAX_TRIES = 1000

# Do you want lots of text telling you what is going on?
# True lots of text (default). Good for debugging.
# False no text
VERBOSE = True

##############################################################
#  Don't edit below here unless you know what you are doing  #
##############################################################

# input filtering
TREE_COUNT = int(TREE_COUNT)
if TREE_COUNT < 0:
    TREE_COUNT = 0
if SHAPE not in ["normal", "bamboo", "palm", "stickly",
                 "round", "cone", "procedural",
                 "rainforest", "mangrove"]:
    if VERBOSE:
        print("SHAPE not set correctly, using 'procedural'.")
    SHAPE = "procedural"
if CENTER_HEIGHT < 1:
    CENTER_HEIGHT = 1
if EDGE_HEIGHT < 1:
    EDGE_HEIGHT = 1
min_height = min(CENTER_HEIGHT, EDGE_HEIGHT)
if HEIGHT_VARIATION > min_height:
    HEIGHT_VARIATION = min_height
if INTERPOLATION not in ["linear"]:
    if VERBOSE:
        print("INTERPOLATION not set correctly, using 'linear'.")
    INTERPOLATION = "linear"
if WOOD not in [True, False]:
    if VERBOSE:
        print("WOOD not set correctly, using True")
    WOOD = True
if TRUNK_THICKNESS < 0.0:
    TRUNK_THICKNESS = 0.0
if TRUNK_HEIGHT < 0.0:
    TRUNK_HEIGHT = 0.0
if ROOTS not in ["yes", "to_stone", "hanging", "no"]:
    if VERBOSE:
        print("ROOTS not set correctly, using 'no' and creating no roots")
    ROOTS = "no"
if ROOT_BUTTRESSES not in [True, False]:
    if VERBOSE:
        print("ROOT_BUTTRESSES not set correctly, using False")
    ROOT_BUTTRESSES = False
if FOLIAGE not in [True, False]:
    if VERBOSE:
        print("FOLIAGE not set correctly, using True")
    ROOT_BUTTRESSES = True
if FOLIAGE_DENSITY < 0.0:
    FOLIAGE_DENSITY = 0.0
if BRANCH_DENSITY < 0.0:
    BRANCH_DENSITY = 0.0
if MAP_HEIGHT_LIMIT not in [True, False]:
    if VERBOSE:
        print("MAP_HEIGHT_LIMIT not set correctly, using False")
    MAP_HEIGHT_LIMIT = False
if LIGHT_TREE not in [0, 1, 2, 4]:
    if VERBOSE:
        print("LIGHT_TREE not set correctly, using 0 for no torches")
    LIGHT_TREE = 0
# assemble the material dictionaries
WOOD_INFO = {'B': WOOD_MAT, 'D': WOOD_DATA}
LEAF_INFO = {'B': LEAF_MAT, 'D': LEAF_DATA}
LIGHT_INFO = {'B': LIGHT_MAT, 'D': LIGHT_DATA}
TRUNK_FILL_INFO = {'B': TRUNK_FILL_MAT, 'D': TRUNK_FILL_DATA}

# The following is an interface class for .mclevel data for minecraft savefiles.
# The following also includes a useful coordinate to index convertor and several
# other useful functions.

import mcInterface

#some handy functions


def dist_to_mat(cord, vec, mat_id_list, mc_map, invert=False, limit=False):
    '''travel from cord along vec and return how far it was to a point of mat_idx

    the distance is returned in number of iterations.  If the edge of the map
    is reached, then return the number of iterations as well.
    if invert == True, search for anything other than those in mat_id_list
    '''
    assert isinstance(mc_map, mcInterface.SaveFile)
    block = mc_map.block
    cur_cord = [i + .5 for i in cord]
    iterations = 0
    on_map = True
    while on_map:
        x = int(cur_cord[0])
        y = int(cur_cord[1])
        z = int(cur_cord[2])
        return_dict = block(x, y, z)
        if return_dict is None:
            break
        else:
            block_value = return_dict['B']
        if (block_value in mat_id_list) and (invert == False):
            break
        elif (block_value not in mat_id_list) and invert:
            break
        else:
            cur_cord = [cur_cord[i] + vec[i] for i in range(3)]
            iterations += 1
        if limit and iterations > limit:
            break
    return iterations

# This is the end of the MCLevel interface.

# Now, on to the actual code.

from random import random, choice, sample
from math import sqrt, sin, cos, pi


def calc_column_lighting(x, z, mclevel):
    '''Recalculate the sky lighting of the column.'''

    # Begin at the top with sky light level 15.
    cur_light = 15
    # traverse the column until cur_light == 0
    # and the existing light values are also zero.
    y = 127
    get_block = mclevel.block
    set_block = mclevel.set_block
    get_height = mclevel.retrieve_heightmap
    set_height = mclevel.set_heightmap
    #get the current heightmap
    cur_height = get_height(x, z)
    # set a flag that the highest point has been updated
    height_updated = False
    # if this doesn't exist, the block doesn't exist either, abort.
    if cur_height is None:
        return None
    light_reduction_lookup = {0: 0, 20: 0, 18: 1, 8: 2, 79: 2}
    while True:
        #get the block sky light and type
        block_info = get_block(x, y, z, 'BS')
        block_light = block_info['S']
        block_type = block_info['B']
        # update the height map if it hasn't been updated yet,
        # and the current block reduces light
        if (not height_updated) and (block_type not in (0, 20)):
            new_height = y + 1
            if new_height == 128:
                new_height = 127
            set_height(x, new_height, z)
            height_updated = True
        #compare block with cur_light, escape if both 0
        if block_light == 0 and cur_light == 0:
            break
        #set the block light if necessary
        if block_light != cur_light:
            set_block(x, y, z, {'S': cur_light})
        #set the new cur_light
        if block_type in light_reduction_lookup:
            # partial light reduction
            light_reduction = light_reduction_lookup[block_type]
        else:
            # full light reduction
            light_reduction = 16
        cur_light += -light_reduction
        if cur_light < 0:
            cur_light = 0
        #increment and check y
        y += -1
        if y < 0:
            break


class ReLight(object):
    '''keep track of which squares need to be relit, and then relight them'''
    def add(self, x, z):
        coords = (x, z)
        self.all_columns.add(coords)

    def calc_lighting(self):
        mclevel = self.save_file
        for column_coords in self.all_columns:
            # recalculate the lighting
            x = column_coords[0]
            z = column_coords[1]
            calc_column_lighting(x, z, mclevel)

    def __init__(self):
        self.all_columns = set()
        self.save_file = None

relight_master = ReLight()


def assign_value(x, y, z, values, save_file):
    '''Assign an index value to a location in mc_map.

    If the index is outside the bounds of the map, return None.  If the
    assignment succeeds, return True.
    '''
    if y > 127:
        return None
    result = save_file.set_block(x, y, z, values)
    if LIGHTING_FIX:
        relight_master.add(x, z)
    return result


class Tree(object):
    '''Set up the interface for tree objects.  Designed for subclassing.
    '''
    def prepare(self, mc_map):
        '''initialize the internal values for the Tree object.
        '''
        return None

    def make_trunk(self, mc_map):
        '''Generate the trunk and enter it in mc_map.
        '''
        return None

    def make_foliage(self, mc_map):
        """Generate the foliage and enter it in mc_map.

        Note, foliage will disintegrate if there is no log nearby"""
        return None

    def copy(self, other):
        '''Copy the essential values of the other tree object into self.
        '''
        self.pos = other.pos
        self.height = other.height

    def __init__(self, pos=[0, 0, 0], height=1):
        '''Accept values for the position and height of a tree.

        Store them in self.
        '''
        self.pos = pos
        self.height = height


class StickTree(Tree):
    '''Set up the trunk for trees with a trunk width of 1 and simple geometry.

    Designed for subclassing.  Only makes the trunk.
    '''
    def make_trunk(self, mc_map):
        x = self.pos[0]
        y = self.pos[1]
        z = self.pos[2]
        for i in range(self.height):
            assign_value(x, y, z, WOOD_INFO, mc_map)
            y += 1


class NormalTree(StickTree):
    '''Set up the foliage for a 'normal' tree.

    This tree will be a single bulb of foliage above a single width trunk.
    This shape is very similar to the default Minecraft tree.
    '''
    def make_foliage(self, mc_map):
        """note, foliage will disintegrate if there is no foliage below, or
        if there is no "log" block within range 2 (square) at the same level or
        one level below"""
        top_y = self.pos[1] + self.height - 1
        start = top_y - 2
        end = top_y + 2
        for y in range(start, end):
            if y > start + 1:
                rad = 1
            else:
                rad = 2
            for x_off in range(-rad, rad + 1):
                for z_off in range(-rad, rad + 1):
                    if (random() > 0.618
                        and abs(x_off) == abs(z_off)
                        and abs(x_off) == rad
                        ):
                        continue

                    x = self.pos[0] + x_off
                    z = self.pos[2] + z_off

                    assign_value(x, y, z, LEAF_INFO, mc_map)


class BambooTree(StickTree):
    '''Set up the foliage for a bamboo tree.

    Make foliage sparse and adjacent to the trunk.
    '''
    def make_foliage(self, mc_map):
        start = self.pos[1]
        end = self.pos[1] + self.height + 1
        for y in range(start, end):
            for i in [0, 1]:
                x_off = choice([-1, 1])
                z_off = choice([-1, 1])
                x = self.pos[0] + x_off
                z = self.pos[2] + z_off
                assign_value(x, y, z, LEAF_INFO, mc_map)


class PalmTree(StickTree):
    '''Set up the foliage for a palm tree.

    Make foliage stick out in four directions from the top of the trunk.
    '''
    def make_foliage(self, mc_map):
        y = self.pos[1] + self.height
        for x_off in range(-2, 3):
            for z_off in range(-2, 3):
                if abs(x_off) == abs(z_off):
                    x = self.pos[0] + x_off
                    z = self.pos[2] + z_off
                    assign_value(x, y, z, LEAF_INFO, mc_map)


class ProceduralTree(Tree):
    '''Set up the methods for a larger more complicated tree.

    This tree type has roots, a trunk, and branches all of varying width,
    and many foliage clusters.
    MUST BE SUBCLASSED.  Specifically, self.foliage_shape must be set.
    Subclass 'prepare' and 'shape_func' to make different shaped trees.
    '''

    def cross_section(self, center, radius, dir_axis, mat_idx, mc_map):
        '''Create a round section of type mat_idx in mc_map.

        Passed values:
        center = [x, y, z] for the coordinates of the center block
        radius = <number> as the radius of the section.  May be a float or int.
        dir_axis: The list index for the axis to make the section
        perpendicular to.  0 indicates the x axis, 1 the y, 2 the z.  The
        section will extend along the other two axes.
        mat_idx = <int> the integer value to make the section out of.
        mc_map = the array generated by make_mc_map
        '''
        rad = int(radius + .618)
        if rad <= 0:
            return None
        sec_idx1 = (dir_axis - 1) % 3
        sec_idx2 = (1 + dir_axis) % 3
        coord = [0, 0, 0]
        for off1 in range(-rad, rad + 1):
            for off2 in range(-rad, rad + 1):
                this_dist = sqrt((abs(off1) + .5) ** 2 + (abs(off2) + .5) ** 2)
                if this_dist > radius:
                    continue
                pri = center[dir_axis]
                sec1 = center[sec_idx1] + off1
                sec2 = center[sec_idx2] + off2
                coord[dir_axis] = pri
                coord[sec_idx1] = sec1
                coord[sec_idx2] = sec2
                assign_value(coord[0], coord[1], coord[2], mat_idx, mc_map)

    def shape_func(self, y):
        '''Take y and return a radius for the location of the foliage cluster.

        If no foliage cluster is to be created, return None
        Designed for subclassing.  Only makes clusters close to the trunk.
        '''
        if random() < 100. / (self.height ** 2) and y < self.trunk_height:
            return self.height * .12
        return None

    def foliage_cluster(self, center, mc_map):
        '''generate a round cluster of foliage at the location center.

        The shape of the cluster is defined by the list self.foliage_shape.
        This list must be set in a subclass of ProceduralTree.
        '''
        level_radius = self.foliage_shape
        x = center[0]
        y = center[1]
        z = center[2]
        for i in level_radius:
            self.cross_section([x, y, z], i, 1, LEAF_INFO, mc_map)
            y += 1

    def tapered_cylinder(self, start, end, start_size, end_size, mc_map, block_data):
        '''Create a tapered cylinder in mc_map.

        start and end are the beginning and ending coordinates of form [x, y, z].
        start_size and end_size are the beginning and ending radius.
        The material of the cylinder is WOOD_MAT.
        '''

        # delta is the coordinate vector for the difference between
        # start and end.
        delta = [int(end[i] - start[i]) for i in range(3)]
        # prim_idx is the index (0, 1, or 2 for x, y, z) for the coordinate
        # which has the largest overall delta.
        max_dist = max(delta, key=abs)
        if max_dist == 0:
            return None
        prim_idx = delta.index(max_dist)
        # sec_idx1 and sec_idx1 are the remaining indices out of [0, 1, 2].
        sec_idx1 = (prim_idx - 1) % 3
        sec_idx2 = (1 + prim_idx) % 3
        # prim_sign is the digit 1 or -1 depending on whether the limb is headed
        # along the positive or negative prim_idx axis.
        prim_sign = int(delta[prim_idx] / abs(delta[prim_idx]))
        # sec_delta1 and ...2 are the amount the associated values change
        # for every step along the prime axis.
        sec_delta1 = delta[sec_idx1]
        sec_fac1 = float(sec_delta1) / delta[prim_idx]
        sec_delta2 = delta[sec_idx2]
        sec_fac2 = float(sec_delta2) / delta[prim_idx]
        # Initialize coord.  These values could be anything, since
        # they are overwritten.
        coord = [0, 0, 0]
        # Loop through each cross_section along the primary axis,
        # from start to end.
        end_offset = delta[prim_idx] + prim_sign
        for prim_offset in range(0, end_offset, prim_sign):
            prim_loc = start[prim_idx] + prim_offset
            sec_loc1 = int(start[sec_idx1] + prim_offset * sec_fac1)
            sec_loc2 = int(start[sec_idx2] + prim_offset * sec_fac2)
            coord[prim_idx] = prim_loc
            coord[sec_idx1] = sec_loc1
            coord[sec_idx2] = sec_loc2
            prim_dist = abs(delta[prim_idx])
            radius = end_size + (start_size - end_size) * abs(delta[prim_idx]
                                - prim_offset) / prim_dist
            self.cross_section(coord, radius, prim_idx, block_data, mc_map)

    def make_foliage(self, mc_map):
        '''Generate the foliage for the tree in mc_map.
        '''
        """note, foliage will disintegrate if there is no foliage below, or
        if there is no "log" block within range 2 (square) at the same level or
        one level below"""
        foliage_coords = self.foliage_cords
        for coord in foliage_coords:
            self.foliage_cluster(coord, mc_map)
        for cord in foliage_coords:
            assign_value(cord[0], cord[1], cord[2], WOOD_INFO, mc_map)
            if LIGHT_TREE == 1:
                assign_value(cord[0], cord[1] + 1, cord[2], LIGHT_INFO, mc_map)
            elif LIGHT_TREE in [2, 4]:
                assign_value(cord[0] + 1, cord[1], cord[2], LIGHT_INFO, mc_map)
                assign_value(cord[0] - 1, cord[1], cord[2], LIGHT_INFO, mc_map)
                if LIGHT_TREE == 4:
                    assign_value(cord[0], cord[1], cord[2] + 1, LIGHT_INFO, mc_map)
                    assign_value(cord[0], cord[1], cord[2] - 1, LIGHT_INFO, mc_map)

    def make_branches(self, mc_map):
        '''Generate the branches and enter them in mc_map.
        '''
        tree_position = self.pos
        height = self.height
        top_y = tree_position[1] + int(self.trunk_height + 0.5)
        # end_rad is the base radius of the branches at the trunk
        end_rad = self.trunk_radius * (1 - self.trunk_height / height)
        if end_rad < 1.0:
            end_rad = 1.0
        for coord in self.foliage_cords:
            dist = (sqrt(float(coord[0] - tree_position[0]) ** 2 +
                            float(coord[2] - tree_position[2]) ** 2))
            y_dist = coord[1] - tree_position[1]
            # value is a magic number that weights the probability
            # of generating branches properly so that
            # you get enough on small trees, but not too many
            # on larger trees.
            # Very difficult to get right... do not touch!
            value = (self.branch_density * 220 * height) / ((y_dist + dist) ** 3)
            if value < random():
                continue

            posy = coord[1]
            slope = self.branch_slope + (0.5 - random()) * .16
            if coord[1] - dist * slope > top_y:
                # Another random rejection, for branches between
                # the top of the trunk and the crown of the tree
                threshold = 1 / float(height)
                if random() < threshold:
                    continue
                branchy = top_y
                base_size = end_rad
            else:
                branchy = posy - dist * slope
                base_size = (end_rad + (self.trunk_radius - end_rad) *
                         (top_y - branchy) / self.trunk_height)
            start_size = (base_size * (1 + random()) * .618 *
                         (dist / height) ** 0.618)
            rndr = sqrt(random()) * base_size * 0.618
            rnd_ang = random() * 2 * pi
            rnd_x = int(rndr * sin(rnd_ang) + 0.5)
            rnd_z = int(rndr * cos(rnd_ang) + 0.5)
            start_coord = [tree_position[0] + rnd_x,
                          int(branchy),
                          tree_position[2] + rnd_z]
            if start_size < 1.0:
                start_size = 1.0
            end_size = 1.0
            self.tapered_cylinder(start_coord, coord, start_size, end_size,
                             mc_map, WOOD_INFO)

    def make_roots(self, root_bases, mc_map):
        '''generate the roots and enter them in mc_map.

        root_bases = [[x, z, base_radius], ...] and is the list of locations
        the roots can originate from, and the size of that location.
        '''
        tree_position = self.pos
        height = self.height
        for coord in self.foliage_cords:
            # First, set the threshold for randomly selecting this
            # coordinate for root creation.
            dist = (sqrt(float(coord[0] - tree_position[0]) ** 2 +
                            float(coord[2] - tree_position[2]) ** 2))
            y_dist = coord[1] - tree_position[1]
            value = (self.branch_density * 220 * height) / ((y_dist + dist) ** 3)
            # Randomly skip roots, based on the above threshold
            if value < random():
                continue
            # initialize the internal variables from a selection of
            # starting locations.
            root_base = choice(root_bases)
            root_x = root_base[0]
            root_z = root_base[1]
            root_base_radius = root_base[2]
            # Offset the root origin location by a random amount
            # (radially) from the starting location.
            rndr = (sqrt(random()) * root_base_radius * .618)
            rnd_ang = random() * 2 * pi
            rnd_x = int(rndr * sin(rnd_ang) + 0.5)
            rnd_z = int(rndr * cos(rnd_ang) + 0.5)
            rnd_y = int(random() * root_base_radius * 0.5)
            start_coord = [root_x + rnd_x, tree_position[1] + rnd_y, root_z + rnd_z]
            # offset is the distance from the root base to the root tip.
            offset = [start_coord[i] - coord[i] for i in range(3)]
            # If this is a mangrove tree, make the roots longer.
            if SHAPE == "mangrove":
                offset = [int(val * 1.618 - 1.5) for val in offset]
            end_coord = [start_coord[i] + offset[i] for i in range(3)]
            root_start_size = (root_base_radius * 0.618 * abs(offset[1]) /
                             (height * 0.618))
            if root_start_size < 1.0:
                root_start_size = 1.0
            end_size = 1.0
            # If ROOTS is set to "to_stone" or "hanging" we need to check
            # along the distance for collision with existing materials.
            if ROOTS in ["to_stone", "hanging"]:
                off_length = sqrt(float(offset[0]) ** 2 +
                                 float(offset[1]) ** 2 +
                                 float(offset[2]) ** 2)
                if off_length < 1:
                    continue
                root_mid = end_size
                # vec is a unit vector along the direction of the root.
                vec = [offset[i] / off_length for i in range(3)]
                if ROOTS == "to_stone":
                    search_index = STOPS_ROOTS
                elif ROOTS == "hanging":
                    search_index = [0]
                # start_dist is how many steps to travel before starting to
                # search for the material.  It is used to ensure that large
                # roots will go some distance before changing directions
                # or stopping.
                start_dist = int(random() * 6 * sqrt(root_start_size) + 2.8)
                # search_start is the coordinate where the search should begin
                search_start = [start_coord[i] + start_dist * vec[i]
                               for i in range(3)]
                # dist stores how far the search went (including search_start)
                # before encountering the expected material.
                dist = start_dist + dist_to_mat(search_start, vec,
                                        search_index, mc_map, limit=off_length)
                # If the distance to the material is less than the length
                # of the root, change the end point of the root to where
                # the search found the material.
                if dist < off_length:
                    # root_mid is the size of the cross_section at end_coord.
                    root_mid += (root_start_size -
                                         end_size) * (1 - dist / off_length)
                    # end_coord is the midpoint for hanging roots,
                    # and the endpoint for roots stopped by stone.
                    end_coord = [start_coord[i] + int(vec[i] * dist)
                                for i in range(3)]
                    if ROOTS == "hanging":
                        # remaining_dist is how far the root had left
                        # to go when it was stopped.
                        remaining_dist = off_length - dist
                        # Initialize bottom_cord to the stopping point of
                        # the root, and then hang straight down
                        # a distance of remaining_dist.
                        bottom_cord = end_coord[:]
                        bottom_cord[1] += -int(remaining_dist)
                        # Make the hanging part of the hanging root.
                        self.tapered_cylinder(end_coord, bottom_cord,
                             root_mid, end_size, mc_map, WOOD_INFO)

                # make the beginning part of hanging or "to_stone" roots
                self.tapered_cylinder(start_coord, end_coord,
                     root_start_size, root_mid, mc_map, WOOD_INFO)

            # If you aren't searching for stone or air, just make the root.
            else:
                self.tapered_cylinder(start_coord, end_coord,
                             root_start_size, end_size, mc_map, WOOD_INFO)

    def make_trunk(self, mc_map):
        '''Generate the trunk, roots, and branches in mc_map.
        '''
        height = self.height
        trunk_height = self.trunk_height
        trunk_radius = self.trunk_radius
        tree_position = self.pos
        start_y = tree_position[1]
        mid_y = tree_position[1] + int(trunk_height * .382)
        top_y = tree_position[1] + int(trunk_height + 0.5)
        # In this method, x and z are the position of the trunk.
        x = tree_position[0]
        z = tree_position[2]
        end_size_factor = trunk_height / height
        mid_rad = trunk_radius * (1 - end_size_factor * .5)
        end_rad = trunk_radius * (1 - end_size_factor)
        if end_rad < 1.0:
            end_rad = 1.0
        if mid_rad < end_rad:
            mid_rad = end_rad
        # Make the root buttresses, if indicated
        if ROOT_BUTTRESSES or SHAPE == "mangrove":
            # The start radius of the trunk should be a little smaller if we
            # are using root buttresses.
            start_rad = trunk_radius * .8
            # root_bases is used later in self.make_roots(...) as
            # starting locations for the roots.
            root_bases = [[x, z, start_rad]]
            buttress_radius = trunk_radius * 0.382
            # pos_radius is how far the root buttresses should be offset
            # from the trunk.
            pos_radius = trunk_radius
            # In mangroves, the root buttresses are much more extended.
            if SHAPE == "mangrove":
                pos_radius = pos_radius * 2.618
            num_of_buttresses = int(sqrt(trunk_radius) + 3.5)
            for i in range(num_of_buttresses):
                rnd_ang = random() * 2 * pi
                this_pos_radius = pos_radius * (0.9 + random() * .2)
                # this_x and this_z are the x and z position for the base of
                # the root buttress.
                this_x = x + int(this_pos_radius * sin(rnd_ang))
                this_z = z + int(this_pos_radius * cos(rnd_ang))
                # this_buttress_radius is the radius of the buttress.
                # Currently, root buttresses do not taper.
                this_buttress_radius = buttress_radius * (0.618 + random())
                if this_buttress_radius < 1.0:
                    this_buttress_radius = 1.0
                # Make the root buttress.
                self.tapered_cylinder([this_x, start_y, this_z], [x, mid_y, z],
                                 this_buttress_radius, this_buttress_radius,
                                 mc_map, WOOD_INFO)
                # Add this root buttress as a possible location at
                # which roots can spawn.
                root_bases += [[this_x, this_z, this_buttress_radius]]
        else:
            # If root buttresses are turned off, set the trunk radius
            # to normal size.
            start_rad = trunk_radius
            root_bases = [[x, z, start_rad]]
        # Make the lower and upper sections of the trunk.
        self.tapered_cylinder([x, start_y, z], [x, mid_y, z], start_rad, mid_rad,
                         mc_map, WOOD_INFO)
        self.tapered_cylinder([x, mid_y, z], [x, top_y, z], mid_rad, end_rad,
                         mc_map, WOOD_INFO)
        #Make the branches
        self.make_branches(mc_map)
        #Make the roots, if indicated.
        if ROOTS in ["yes", "to_stone", "hanging"]:
            self.make_roots(root_bases, mc_map)
        # Hollow the trunk, if specified
        # check to make sure that the trunk is large enough to be hollow
        if trunk_radius > 2 and HOLLOW_TRUNK:
            # wall thickness is actually the double the wall thickness
            # it is a diameter difference, not a radius difference.
            wall_thickness = (1 + trunk_radius * 0.1 * random())
            if wall_thickness < 1.3:
                wall_thickness = 1.3
            base_radius = trunk_radius - wall_thickness
            if base_radius < 1:
                base_radius = 1.0
            mid_radius = mid_rad - wall_thickness
            top_radius = end_rad - wall_thickness
            # the starting x and y can be offset by up to the wall thickness.
            base_offset = int(wall_thickness)
            x_choices = [i for i in range(x - base_offset,
                                          x + base_offset + 1)]
            start_x = choice(x_choices)
            z_choices = [i for i in range(z - base_offset,
                                          z + base_offset + 1)]
            start_z = choice(z_choices)
            self.tapered_cylinder([start_x, start_y, start_z], [x, mid_y, z],
                                 base_radius, mid_radius,
                         mc_map, TRUNK_FILL_INFO)
            hollow_top_y = int(top_y + trunk_radius + 1.5)
            self.tapered_cylinder([x, mid_y, z], [x, hollow_top_y, z],
                                 mid_radius, top_radius,
                                 mc_map, TRUNK_FILL_INFO)

    def prepare(self, mc_map):
        '''Initialize the internal values for the Tree object.

        Primarily, sets up the foliage cluster locations.
        '''
        tree_position = self.pos
        self.trunk_radius = .618 * sqrt(self.height * TRUNK_THICKNESS)
        if self.trunk_radius < 1:
            self.trunk_radius = 1
        if BROKEN_TRUNK:
            self.trunk_height = self.height * (.3 + random() * .4)
            y_end = int(tree_position[1] + self.trunk_height + .5)
        else:
            self.trunk_height = self.height
            y_end = int(tree_position[1] + self.height)
        self.branch_density = BRANCH_DENSITY / FOLIAGE_DENSITY
        top_y = tree_position[1] + int(self.trunk_height + 0.5)
        foliage_coords = []
        y_start = tree_position[1]
        num_of_clusters_per_y = int(1.5 + (FOLIAGE_DENSITY *
                                           self.height / 19.) ** 2)
        if num_of_clusters_per_y < 1:
            num_of_clusters_per_y = 1
        # make sure we don't spend too much time off the top of the map
        if y_end > 127:
            y_end = 127
        if y_start > 127:
            y_start = 127
        for y in range(y_end, y_start, -1):
            for i in range(num_of_clusters_per_y):
                shape_fac = self.shape_func(y - y_start)
                if shape_fac is None:
                    continue
                r = (sqrt(random()) + .328) * shape_fac

                theta = random() * 2 * pi
                x = int(r * sin(theta)) + tree_position[0]
                z = int(r * cos(theta)) + tree_position[2]
                # if there are values to search in STOPS_BRANCHES
                # then check to see if this cluster is blocked
                # by stuff, like dirt or rock, or whatever
                if len(STOPS_BRANCHES):
                    dist = (sqrt(float(x - tree_position[0]) ** 2 +
                                float(z - tree_position[2]) ** 2))
                    slope = self.branch_slope
                    if y - dist * slope > top_y:
                        # the top of the tree
                        start_y = top_y
                    else:
                        start_y = y - dist * slope
                    # the start position of the search
                    start = [tree_position[0], start_y, tree_position[2]]
                    offset = [x - tree_position[0],
                              y - start_y,
                              z - tree_position[2]]
                    off_length = sqrt(offset[0] ** 2 + offset[1] ** 2 + offset[2] ** 2)
                    # if the branch is as short as... nothing, don't bother.
                    if off_length < 1:
                        continue
                    # unit vector for the search
                    vec = [offset[i] / off_length for i in range(3)]
                    mat_dist = dist_to_mat(start, vec, STOPS_BRANCHES,
                                           mc_map, limit=off_length + 3)
                    # after all that, if you find something, don't add
                    # this coordinate to the list
                    if mat_dist < off_length + 2:
                        continue
                foliage_coords += [[x, y, z]]

        self.foliage_cords = foliage_coords


class RoundTree(ProceduralTree):
    '''This kind of tree is designed to resemble a deciduous tree.
    '''
    def prepare(self, mc_map):
        self.branch_slope = 0.382
        ProceduralTree.prepare(self, mc_map)
        self.foliage_shape = [2, 3, 3, 2.5, 1.6]
        self.trunk_radius = self.trunk_radius * 0.8
        self.trunk_height = TRUNK_HEIGHT * self.trunk_height

    def shape_func(self, y):
        twigs = ProceduralTree.shape_func(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.282 + .1 * sqrt(random())):
            return None
        radius = self.height / 2.
        adj = self.height / 2. - y
        if adj == 0:
            dist = radius
        elif abs(adj) >= radius:
            dist = 0
        else:
            dist = sqrt((radius ** 2) - (adj ** 2))
        dist = dist * .618
        return dist


class ConeTree(ProceduralTree):
    '''this kind of tree is designed to resemble a conifer tree.
    '''
    # woodType is the kind of wood the tree has, a data value
    woodType = 1

    def prepare(self, mc_map):
        self.branch_slope = 0.15
        ProceduralTree.prepare(self, mc_map)
        self.foliage_shape = [3, 2.6, 2, 1]
        self.trunk_radius = self.trunk_radius * 0.5

    def shape_func(self, y):
        twigs = ProceduralTree.shape_func(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.25 + .05 * sqrt(random())):
            return None
        radius = (self.height - y) * 0.382
        if radius < 0:
            radius = 0
        return radius


class RainforestTree(ProceduralTree):
    '''This kind of tree is designed to resemble a rainforest tree.
    '''
    def prepare(self, mc_map):
        self.foliage_shape = [3.4, 2.6]
        self.branch_slope = 1.0
        ProceduralTree.prepare(self, mc_map)
        self.trunk_radius = self.trunk_radius * 0.382
        self.trunk_height = self.trunk_height * .9

    def shape_func(self, y):
        if y < self.height * 0.8:
            if EDGE_HEIGHT < self.height:
                twigs = ProceduralTree.shape_func(self, y)
                if (twigs is not None) and random() < 0.07:
                    return twigs
            return None
        else:
            width = self.height * .382
            top_dist = (self.height - y) / (self.height * 0.2)
            dist = width * (0.618 + top_dist) * (0.618 + random()) * 0.382
            return dist


class MangroveTree(RoundTree):
    '''This kind of tree is designed to resemble a mangrove tree.
    '''
    def prepare(self, mc_map):
        self.branch_slope = 1.0
        RoundTree.prepare(self, mc_map)
        self.trunk_radius = self.trunk_radius * 0.618

    def shape_func(self, y):
        val = RoundTree.shape_func(self, y)
        if val is None:
            return val
        val = val * 1.618
        return val


def plant_trees(mc_map, tree_list):
    '''Take mc_map and add trees to random locations on the surface to tree_list.
    '''
    assert isinstance(mc_map, mcInterface.SaveFile)
    # keep looping until all the trees are placed
    # calc the radius difference, for interpolation
    in_out_dif = EDGE_HEIGHT - CENTER_HEIGHT
    if VERBOSE:
        print('Tree Locations: x, y, z, tree height')
    tries = 0
    max_tries = MAX_TRIES
    while len(tree_list) < TREE_COUNT:
        if tries > max_tries:
            if VERBOSE:
                print(("Stopping search for tree locations after {0} tries".format(tries)))
                print("If you don't have enough trees, check X, Y, RADIUS, and PLANT_ON")
            break
        tries += 1
        # choose a location
        rad_fraction = random()
        # this is some kind of square interpolation
        rad_fraction = 1.0 - rad_fraction
        rad_fraction **= 2
        rad_fraction = 1.0 - rad_fraction

        rad = rad_fraction * RADIUS
        ang = random() * pi * 2
        x = X + int(rad * sin(ang) + .5)
        z = Z + int(rad * cos(ang) + .5)
        # check to see if this location is suitable
        y_top = mc_map.surface_block(x, z)
        if y_top is None:
            # this location is off the map!
            continue
        if y_top['B'] in PLANT_ON:
            # plant the tree on the block above the ground
            # hence the " + 1"
            y = y_top['y'] + 1
        else:
            continue
        # this is linear interpolation also.
        base_height = CENTER_HEIGHT + (in_out_dif * rad_fraction)
        height_rand = (random() - .5) * 2 * HEIGHT_VARIATION
        height = int(base_height + height_rand)
        # if the option is set, check the surrounding area for trees
        if ONLY_IN_FORESTS:
            '''we are looking for foliage
            it should show up in the "surface_block" search
            check every fifth block in a square pattern,
            offset around the trunk
            and equal to the trees height
            if the area is not at least one third foliage,
            don't build the tree'''
            # spacing is how far apart each sample should be
            spacing = 5
            # search_size is how many blocks to check
            # along each axis
            search_size = 2 + (height // spacing)
            # check at least 3 x 3
            search_size = max([search_size, 3])
            # set up the offset values to offset the starting corner
            offset = ((search_size - 1) * spacing) // 2
            # foliage_count is the total number of foliage blocks found
            foliage_count = 0
            # check each sample location for foliage
            for step_x in range(search_size):
                # search_x is the x location to search this sample
                search_x = x - offset + (step_x * spacing)
                for step_z in range(search_size):
                    # same as for search_x
                    search_z = z - offset + (step_z * spacing)
                    search_block = mc_map.surface_block(search_x, search_z)
                    if search_block is None:
                        continue
                    if search_block['B'] == 18:
                        # this sample contains foliage!
                        # add it to the total
                        foliage_count += 1
            #now that we have the total count, find the ratio
            total_searched = search_size ** 2
            foliage_ratio = foliage_count / total_searched
            # the acceptable amount is about a third
            acceptable_ratio = .3
            if foliage_ratio < acceptable_ratio:
                # after all that work, there wasn't enough foliage around!
                # try again!
                continue

        # generate the new tree
        new_tree = Tree([x, y, z], height)
        if VERBOSE:
            print((x, y, z, height))
        tree_list += [new_tree]


def process_trees(mc_map, tree_list):
    '''Initalize all of the trees in tree_list.

    Set all of the trees to the right type, and run prepare.  If indicated
    limit the height of the trees to the top of the map.
    '''
    assert isinstance(mc_map, mcInterface.SaveFile)
    if SHAPE == "stickly":
        shape_choices = ["normal", "bamboo", "palm"]
    elif SHAPE == "procedural":
        shape_choices = ["round", "cone"]
    else:
        shape_choices = [SHAPE]

    # initialize map_height, just in case
    map_height = 127
    for i in range(len(tree_list)):
        new_shape = choice(shape_choices)
        if new_shape == "normal":
            new_tree = NormalTree()
        elif new_shape == "bamboo":
            new_tree = BambooTree()
        elif new_shape == "palm":
            new_tree = PalmTree()
        elif new_shape == "round":
            new_tree = RoundTree()
        elif new_shape == "cone":
            new_tree = ConeTree()
        elif new_shape == "rainforest":
            new_tree = RainforestTree()
        elif new_shape == "mangrove":
            new_tree = MangroveTree()

        # Get the height and position of the existing trees in
        # the list.
        new_tree.copy(tree_list[i])
        # Now check each tree to ensure that it doesn't stick
        # out the top of the map.  If it does, shorten it until
        # the top of the foliage just touches the top of the map.
        if MAP_HEIGHT_LIMIT:
            height = new_tree.height
            y_base = new_tree.pos[1]
            if SHAPE == "rainforest":
                foliage_height = 2
            else:
                foliage_height = 4
            if y_base + height + foliage_height > map_height:
                new_height = map_height - y_base - foliage_height
                new_tree.height = new_height
        # Even if it sticks out the top of the map, every tree
        # should be at least one unit tall.
        if new_tree.height < 1:
            new_tree.height = 1
        new_tree.prepare(mc_map)
        tree_list[i] = new_tree


def main(the_map):
    '''create the trees
    '''
    tree_list = []
    if VERBOSE:
        print("Planting new trees")
    plant_trees(the_map, tree_list)
    if VERBOSE:
        print("Processing tree changes")
    process_trees(the_map, tree_list)
    if FOLIAGE:
        if VERBOSE:
            print("Generating foliage ")
        for i in tree_list:
            i.make_foliage(the_map)
        if VERBOSE:
            print(' completed')
    if WOOD:
        if VERBOSE:
            print("Generating trunks, roots, and branches ")
        for i in tree_list:
            i.make_trunk(the_map)
        if VERBOSE:
            print(' completed')
    return None


def standalone():
    if VERBOSE:
        print("Importing the map")
    try:
        the_map = mcInterface.SaveFile(LOADNAME)
    except IOError:
        if VERBOSE:
            print('File name invalid or save file otherwise corrupted. Aborting')
        return None
    main(the_map)
    if LIGHTING_FIX:
        if VERBOSE:
            print("Rough re-lighting the map")
        relight_master.save_file = the_map
        relight_master.calc_lighting()
    if VERBOSE:
        print("Saving the map, this could be a while")
    the_map.write()
    if VERBOSE:
        print("finished")

if __name__ == '__main__':
    standalone()

# to do:
# get height limits from map
# set "limit height" or some such to respect level height limits
