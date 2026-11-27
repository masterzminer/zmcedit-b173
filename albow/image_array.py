
from pygame import Rect
from albow.resource import get_image


class ImageArray(object):

    def __init__(self, image, shape):
        self.image = image
        self.shape = shape
        if isinstance(shape, tuple):
            self.nrows, self.ncols = shape
        else:
            self.nrows = 1
            self.ncols = shape
        i_width, i_height = image.get_size()
        self.size = i_width // self.ncols, i_height // self.nrows

    def __len__(self):
        return self.shape

    def __getitem__(self, index):
        image = self.image
        nrows = self.nrows
        ncols = self.ncols
        if nrows == 1:
            row = 0
            col = index
        else:
            row, col = index
        width, height = self.size
        left = width * col
        top = height * row
        return image.subsurface(left, top, width, height)

    def get_rect(self):
        return Rect((0, 0), self.size)


image_array_cache = {}


def get_image_array(name, shape, **kwds):
    result = image_array_cache.get(name)
    if not result:
        result = ImageArray(get_image(name, **kwds), shape)
        image_array_cache[name] = result
    return result
