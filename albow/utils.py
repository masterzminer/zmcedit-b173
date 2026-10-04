
from pygame import draw, Surface
from pygame.locals import SRCALPHA


def frame_rect(surface, color, rect, thick=1):
    o = 1
    surface.fill(color, (rect.left + o, rect.top, rect.width - o - o, thick))
    surface.fill(color, (rect.left + o, rect.bottom - thick, rect.width - o - o, thick))
    surface.fill(color, (rect.left, rect.top + o, thick, rect.height - o - o))
    surface.fill(color, (rect.right - thick, rect.top + o, thick, rect.height - o - o))


def blit_in_rect(dst, src, frame, align='tl', margin=0):
    r = src.get_rect()
    align_rect(r, frame, align, margin)
    dst.blit(src, r)


def align_rect(r, frame, align='tl', margin=0):
    if 'l' in align:
        r.left = frame.left + margin
    elif 'r' in align:
        r.right = frame.right - margin
    else:
        r.centerx = frame.centerx
    if 't' in align:
        r.top = frame.top + margin
    elif 'b' in align:
        r.bottom = frame.bottom - margin
    else:
        r.centery = frame.centery


def brighten(rgb, factor):
    return [min(255, int(round(factor * c))) for c in rgb]
