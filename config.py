"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

"""
config.py
Configuration settings and storage.
"""

from configparser import RawConfigParser
from config_classes import Section, ListSection, Setting as S, DirectorySetting as DS, IndexSetting as IS, KeySetting as KS, KeyIndexSetting as KIS, JsonSetting as JS

from directories import INI_FILE
import log

# Setup for the config

def init_config():
    # Ensure the ini file exists
    INI_FILE.touch(exist_ok=True)

    # Load the existing config
    config = RawConfigParser()
    config.read(INI_FILE)
    return config


log.info("Loading config")

# Set up the main config
config = init_config()

def save_config():
    """Dump the main config into the ini file"""
    global config
    with open(INI_FILE, 'w') as f:
        config.write(f)


# Define sections and each individual setting and its default
class _KeysSection(Section):
    """Configs for keybindings"""

    # May want to allow these to be bound to different key combinations, i.e. ctrl, alt, and or shift, not going to scope creep myself for now

    NAME = "keys"

    # Normal keys
    forward = KS("w")
    back = KS("s")
    left = KS("a")
    right = KS("d")
    up = KS("q")
    down = KS("z")
    brake = KS("space")
    
    rotate = KS("e")
    roll = KS("r")
    flip = KS("f")
    mirror = KS("g")
    swap = KS("x")
    
    pan_left = KS("j")
    pan_right = KS("l")
    pan_up = KS("i")
    pan_down = KS("k")
    
    reach_reset = KS("mouse3")
    reach_increase = KS("mouse4")
    reach_decrease = KS("mouse5")
    
    confirm_construction = KS("return")
    
    open_level = KS("o")
    new_level = KS("n")
    delete_blocks = KS("delete")
    
    toggle_fps_counter = KS("0")
    toggle_renderer = KS("m")
    swap_view = KS("tab")

    # Hot keys with control
    goto = KS("g", ["ctrl"])
    swap_view_distance = KS("f", ["ctrl"])
    select_all = KS("a", ["ctrl"])
    deselect = KS("d", ["ctrl"])
    cut = KS("x", ["ctrl"])
    copy = KS("c", ["ctrl"])
    paste = KS("v", ["ctrl"])
    reload = KS("r", ["ctrl"])
    undo = KS("z", ["ctrl"])
    save = KS("s", ["ctrl"])
    close_world = KS("w", ["ctrl"])
    info = KS("i", ["ctrl"])
    export = KS("e", ["ctrl"])

    # Hot keys with alt
    long_distance_mode = KS("z", ["alt"])
    tool_option_1 = KS("1", ["alt"])
    tool_option_2 = KS("2", ["alt"])
    tool_option_3 = KS("3", ["alt"])
    tool_option_4 = KS("4", ["alt"])
    tool_option_5 = KS("5", ["alt"])

    # Debug hot keys
    debug_1 = KS("[")
    debug_2 = KS("]")
    

Keys = _KeysSection(config)


class _ToolKeysSection(Section):
    """Key bindings for selecting tools"""

    NAME = "tool keys"

    tool_select = KIS("1", 0)
    tool_brush = KIS("2", 1)
    tool_clone = KIS("3", 2)
    tool_fill = KIS("4", 3)
    tool_filter = KIS("5", 4)
    tool_import = KIS("6", 5)
    tool_player = KIS("7", 6)
    tool_spawn = KIS("8", 7)
    tool_chunk = KIS("9", 8)


ToolKeys = _ToolKeysSection(config)

class _WorldKeysSection(ListSection):
    """Key bindings for selecting recent worlds"""

    NAME = "recent world keys"


WorldKeys = _WorldKeysSection(5, config, default_values=["f1", "f2", "f3", "f4", "f5"])

class _SettingsSection(Section):
    """Generic configurations"""

    NAME = "settings"
    fly_mode = S(False)
    enable_mouse_lag = S(False)
    long_distance_mode = S(False)

    close_minecraft_warning = S(True)

    fov = S(70.0)

    space_height = S(64)

    view_distance = S(16)
    target_fps = S(60)

    window_width = S(1024)
    window_height = S(768)

    show_hidden_ores = S(False)
    fast_leaves = S(False)
    rough_graphics = S(False)
    show_chunk_redraw = S(True)
    draw_sky = S(True)
    draw_fog = S(True)
    show_ceiling = S(True)
    draw_entities = S(True)
    draw_items = S(True)
    draw_tile_entities = S(True)
    draw_tile_ticks = S(False)
    draw_unpopulated_chunks = S(True)
    vertex_buffer_limit = S(384)

    vsync = S(True)
    view_mode = S("Camera")
    classic_mouse = S(False)
    use_old_file_browser = S(False)
    hide_menu_stars = S(False)
    center_mouse_fix = S(False)
    user_filters_dir = S("")

Settings = _SettingsSection(config)

class _ControlsSection(Section):
    """Settings related to controls"""

    NAME = "controls"

    mouse_speed = S(5.0)
    camera_acceleration = S(125.0)
    camera_drag = S(100.0)
    camera_max_speed = S(60.0)
    camera_breaking_speed = S(8.0)
    invert_mouse_pitch = S(False)
    auto_brake = S(True)
    swap_axes = S(False)

Controls = _ControlsSection(config)


class _SelectToolSection(Section):
    """Settings for the select tool"""

    NAME = "select tool"

    show_previous_selection = S(True)
    color = S("white")

SelectToolSettings = _SelectToolSection(config)


class _BrushToolSection(Section):
    """Settings for the brush tool"""

    NAME = "brush tool"

    length = S(3)
    height = S(3)
    width = S(3)
    shape = S("Round")
    """One of 'Round', 'Square', 'Diamond'"""
    mode = S("Fill")
    """One of 'Fill', 'Flood Fill', 'Replace', 'Erode', 'Topsoil', 'Paste' """

    update_offset = S(False)
    choose_block_immediately = S(False)
    alpha = S(0.66, min=0, max=1)

    minimum_spacing = S(1)
    continuous = S(False)
    chance = S(100)
    chance_type = S("full")
    hollow = S(False)

    """One of 'edge', 'full'"""


BrushToolSettings = _BrushToolSection(config)


class _CloneToolSection(Section):
    """Settings for the clone tool"""

    NAME = "clone tool"

    copy_air = S(True)
    copy_water = S(True)
    place_immediately = S(True)


CloneToolSettings = _CloneToolSection(config)


class _FillToolSection(Section):
    """Settings for the fill tool"""

    NAME = "fill tool"

    chose_block_immediately = S(False)


FillToolSettings = _FillToolSection(config)


class _SpawnToolSection(Section):
    """Settings related to the spawn tool"""

    NAME = "spawn tool"

    protection = S(True)


SpawnToolSettings = _SpawnToolSection(config)


class _ColorSettingsSection(Section):
    """Settings for selectable colors, stored as a string of "r, g, b" where r, g, and b are floating point values for the color"""

    NAME = "colors"

    white = S("1.0, 1.0, 1.0")

    blue = S("0.75, 0.75, 1.0")
    green = S("0.75, 1.0, 0.75")
    red = S("1.0, 0.75, 0.75")

    teal = S("0.75, 1.0, 1.0")
    pink = S("1.0, 0.75, 1.0")
    yellow = S("1.0, 1.0, 0.75")

    grey = S("0.6, 0.6, 0.6")
    black = S("0.0, 0.0, 0.0")


ColorSettings = _ColorSettingsSection(config)


class _LastDirectoriesSection(Section):
    """Configs for the last directory accessed for specific categories"""
    
    NAME = "directories"
    world = DS()
    data = DS()
    schematic = DS()
    filter = DS()

LastDir = _LastDirectoriesSection(config)


class _RecentWorldsSection(ListSection):
    """Worlds that were opened recently"""

    NAME = "recent worlds"


RecentWorlds = _RecentWorldsSection(5, config)


class _LastFilterSection(Section):
    """Stores the settings of each last used filter"""
    
    NAME = "last filter"

    selected = S("")
    """The filter that was last selected"""

    all_settings = JS("")
    """A json string holding the settings of all filters as used"""

LastFilter = _LastFilterSection(config)


# Save the config after final init
save_config()


import time
config_seed = int(time.time_ns())
"""A constant seed that can be used for anything random that should be consistent per application launch"""