#
#   Albow - Sound utilities
#

from __future__ import absolute_import
import pygame
from pygame import mixer


def pause_sound():
    try:
        mixer.pause()
    except pygame.error:
        pass


def resume_sound():
    try:
        mixer.unpause()
    except pygame.error:
        pass


def stop_sound():
    try:
        mixer.stop()
    except pygame.error:
        pass
