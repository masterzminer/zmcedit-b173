'''
Created on Jul 22, 2011

@author: Rio
'''

from contextlib import contextmanager

import logging

from .nbt import *
from .materials import *
from .entity import *

from .faces import *
#String constants for common tag names

log = logging.getLogger(__name__)
warn, error, info, debug = log.warn, log.error, log.info, log.debug

Entities = "Entities"
TileEntities = "TileEntities"

Map = "Map"
Width = "Width"
Height = "Height"
Length = "Length"
Blocks = "Blocks"
Data = "Data"
Inventory = 'Inventory'


@contextmanager
def notclosing(f):
    yield f


def decompress_first(func):
    def dec_first(self, *args, **kw):
        self.decompress()
        return func(self, *args, **kw)

    dec_first.__doc__ = func.__doc__
    return dec_first
def unpack_first(func):
    def upk_first(self, *args, **kw):
        self.unpackChunkData()
        return func(self, *args, **kw)

    upk_first.__doc__ = func.__doc__
    return upk_first

class PlayerNotFound(Exception): pass
class ChunkNotPresent(Exception): pass
class RegionMalformed(Exception): pass
class ChunkMalformed(ChunkNotPresent): pass


def exhaust(_iter):
    """Functions named ending in "Iter" return an iterable object that does
    long-running work and yields progress information on each call. exhaust()
    is used to implement the non-Iter equivalents"""
    i = None
    for i in _iter:
        pass
    return i
