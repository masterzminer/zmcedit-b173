# Introduction
This is a port of MC Edit, developed around editing worlds for Minecraft Beta 1.7.3

This ports the original python2 application, build 0.1.5, to python3 and modern libraries

This port was developed around being a fully stand alone application for modifying existing Minecraft worlds.
It intentionally does not interface with the vanilla Minecraft install, jars, or resources. I highly recommend
against using the vanilla launcher when playing old versions of the game. Prism launcher is my go to as of the
date of writing this readme file.

As of this commit, this readme file is mostly a stub, TODO need to expand on this


# Installing

Need to add instructions here

installing.txt has some rough notes made during development


# Removed Features

Many features of the original MC Edit application have been removed and or modified for this non-exhaustive list of reasons
- The feature doesn't exist in beta 1.7.3 i.e. creative mode
- For the sake of simpler development
- Avoiding porting

Some of the features removed
- Support for Anvil format worlds, i.e. worlds with a 256 block height limit
- Pocket edition support
- Inf dev support
- Generating worlds based on jars
