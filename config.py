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

import logging
from configparser import RawConfigParser
from config_classes import Section, ListSection, Setting as S, DirectorySetting as DS

from directories import INI_FILE

log = logging.getLogger(__name__)

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

    NAME = "keys"
    forward = S("w")
    back = S("s")
    left = S("a")
    right = S("d")
    up = S("q")
    down = S("z")
    brake = S("space")
    
    rotate = S("e")
    roll = S("r")
    flip = S("f")
    mirror = S("g")
    swap = S("x")
    
    pan_left = S("j")
    pan_right = S("l")
    pan_up = S("i")
    pan_down = S("k")
    
    reach_reset = S("mouse3")
    reach_increase = S("mouse4")
    reach_decrease = S("mouse5")
    
    confirm_construction = S("return")
    
    open_level = S("o")
    new_level = S("n")
    delete_blocks = S("delete")
    
    toggle_fps_counter = S("0")
    toggle_renderer = S("m")

Keys = _KeysSection(config)


class _SettingsSection(Section):
    """Generic configurations"""

    NAME = "settings"
    fly_mode = S(False)
    enable_mouse_lag = S(False)
    long_distance_mode = S(False)

    close_minecraft_warning = S(True)

    fov = S(70.0)

    space_height = S(64)
    double_buffer = S(True)

    view_distance = S(16)
    target_fps = S(60)

    window_width = S(1024)
    window_height = S(768)
    window_x = S(0)
    window_y = S(0)
    window_show_cmd = S(1)
    set_window_placement = S(True)

    show_hidden_ores = S(False)
    fast_leaves = S(False)
    rough_graphics = S(False)
    show_chunk_redraw = S(True)
    draw_sky = S(True)
    draw_fog = S(True)
    show_ceiling = S(True)
    draw_entities = S(True)
    draw_monsters = S(True)
    draw_items = S(True)
    draw_tile_entities = S(True)
    draw_tile_ticks = S(False)
    draw_unpopulated_chunks = S(True)
    vertex_buffer_limit = S(384)

    vsync = S(0)
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
    update_offset = S(False)
    choose_block_immediately = S(False)
    alpha = S(0.66, min=0, max=1)


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

    chose_block_immediately = S(True)


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


# Save the config after final init
save_config()
