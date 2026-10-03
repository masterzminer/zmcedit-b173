# Introduction
This is a port of MC Edit, developed around editing worlds for Minecraft Beta 1.7.3

Other pre-anvil worlds may or may not work, I have not tested worlds outside Minecraft beta 1.7.3 and do not plan to.

This ports the original python2 application, build 0.1.5, to python3 and modern libraries

This port was developed around being a fully stand alone application for modifying existing Minecraft worlds.
It intentionally does not interface with the vanilla Minecraft install, jars, or resources. I highly recommend
against using the vanilla launcher when playing old versions of the game. Prism launcher is my go to as of the
date of writing this readme file.


# Installing

To install zMCEdit-b173:
1. Download the executable for your os
2. Place the executable where you want to install it
3. Run the executable
4. There should be no other setup required

Alternatively, you can install python and all dependencies, and run `python mcedit.py` to start the application

As of this commit I have the build process working only for Linux.

I eventually intend to attempt to make a build for Windows 10/11, this is a low priority for me.
Currently I have not tested this port on Windows.

I will not attempt to make a build for Mac, though it's python, in theory it should be straight forward, if you want to try.
It's also worth noting that I have not tested any aspect of this port on Mac, there could be issues specific to Mac.
I have no plans to support and or make fixes for Mac.


# Building from source

To build from source
1. Clone this repo
2. Run `./install.sh`
3. This creates a virtual environment
4. Then installs all python dependencies via pip
5. Then builds an executable via pyinstaller
6. The dist directory should contain the stand alone executable

If you already have the virtual environment setup, the pip dependencies installed, and the Cython for the nbt module is already built, just run `./installing/build.sh`


# TODO
Need to add a section about adding custom filters and modifying configuration files


# Removed Features

Many features of the original MC Edit application have been removed and or modified for this non-exhaustive list of reasons
- The feature doesn't exist in beta 1.7.3 i.e. creative mode
- For the sake of simpler development

Some of the features removed
- No support for Anvil format worlds, i.e. worlds with a 256 block height limit
- No pocket edition support
- No inf dev support
- No generating worlds based on jars
- Removed blocks and items that do not exist in Minecraft Beta 1.7.3

Maybe one day I'll port the last release of MC Edit, or make another fork of this port to allow it to modify Anvil worlds. Probably not though, unless I decide I want to make another map in 1.2.5