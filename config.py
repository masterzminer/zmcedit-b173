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
from config_classes import Section, Setting as S, DirectorySetting as DS
from pathlib import Path

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
class KeysSection(Section):
    """Configs for keybindings"""

    NAME = "Keys"
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


class LastDir(Section):
    """Configs for the last directory accessed for specific categories"""
    
    NAME = "directories"
    world = DS(Path.home())
    data = DS(Path.home())
    schematic = DS(Path.home())
    filter = DS(Path.home())


# Setup all sections
Keys = KeysSection(config)
LastDirectories = LastDir(config)


# Save the config after final init
save_config()




def use_classic_mouse():
    if not config.has_option("Settings", "classic mouse"):
        return False
    return config.getboolean("Settings", "classic mouse")

def update_classic_mouse(use: bool):
    config.set("Settings", "classic mouse", use)


def use_old_file_browser():
    if not config.has_option("Settings", "old file browser"):
        return False
    return config.getboolean("Settings", "old file browser")

def update_old_file_browser(use: bool):
    config.set("Settings", "old file browser", use)


def hide_menu_stars():
    if not config.has_option("Settings", "hide menu stars"):
        return False
    return config.getboolean("Settings", "hide menu stars")

def update_hide_menu_stars(use: bool):
    config.set("Settings", "hide menu stars", use)


def center_mouse_fix():
    if not config.has_option("Settings", "center mouse fix"):
        return False
    return config.getboolean("Settings", "center mouse fix")

def update_center_mouse_fix(enable: bool):
    config.set("Settings", "center mouse fix", enable)

