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
mceutils.py

Exception catching, some basic box drawing, texture pack loading, oddball UI elements
"""

# TODO figure out these libpng errors
# libpng warning: iCCP: known incorrect sRGB profile
# libpng warning: iCCP: cHRM chunk does not match sRGB


from albow.controls import ValueDisplay
from albow import alert, ask, Button, Column, Label, root, Row, ValueButton, Widget
from io import BytesIO
from datetime import datetime
import numpy as np
from OpenGL import GL
from pygame import display, image, Surface
import pymclevel
import traceback
from PIL import Image
import directories
from albow import FloatField, IntField, TextField


def alertException(func):
    def _alertException(*args, **kw):
        try:
            return func(*args, **kw)
        except root.Cancel:
            alert("Canceled.")
        except Exception as e:
            ask("Error during {0}: {1!r}".format(func, e)[:1000], ["Okay"], default=0, cancel=0)
            traceback.print_exc()

    return _alertException


def drawFace(box, face, type=GL.GL_QUADS):
    x, y, z, = box.origin
    x2, y2, z2 = box.maximum

    if face == pymclevel.faces.FaceXDecreasing:

        faceVertices = np.array(
            (x, y2, z2,
            x, y2, z,
            x, y, z,
            x, y, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceXIncreasing:

        faceVertices = np.array(
            (x2, y, z2,
            x2, y, z,
            x2, y2, z,
            x2, y2, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceYDecreasing:
        faceVertices = np.array(
            (x2, y, z2,
            x, y, z2,
            x, y, z,
            x2, y, z,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceYIncreasing:
        faceVertices = np.array(
            (x2, y2, z,
            x, y2, z,
            x, y2, z2,
            x2, y2, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceZDecreasing:
        faceVertices = np.array(
            (x, y, z,
            x, y2, z,
            x2, y2, z,
            x2, y, z,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceZIncreasing:
        faceVertices = np.array(
            (x2, y, z2,
            x2, y2, z2,
            x, y2, z2,
            x, y, z2,
            ), dtype='f4')

    faceVertices.shape = (4, 3)
    dim = face >> 1
    dims = [0, 1, 2]
    dims.remove(dim)

    texVertices = np.array(
        faceVertices[:, dims],
        dtype='f4'
    ).flatten()
    faceVertices.shape = (12,)

    texVertices *= 16
    GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    GL.glVertexPointer(3, GL.GL_FLOAT, 0, faceVertices)
    GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, texVertices)

    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glEnable(GL.GL_POLYGON_OFFSET_LINE)

    if type is GL.GL_LINE_STRIP:
        indexes = np.array((0, 1, 2, 3, 0), dtype='uint32')
        GL.glDrawElements(type, 5, GL.GL_UNSIGNED_INT, indexes)
    else:
        GL.glDrawArrays(type, 0, 4)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glDisable(GL.GL_POLYGON_OFFSET_LINE)
    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)


def drawCube(box, cubeType=GL.GL_QUADS, blockType=0, texture=None, textureVertices=None, selectionBox=False):
    """ pass a different cubeType e.g. GL_LINE_STRIP for wireframes """
    x, y, z, = box.origin
    x2, y2, z2 = box.maximum
    dx, dy, dz = x2 - x, y2 - y, z2 - z
    cubeVertices = np.array(
        (
        x, y, z,
        x, y2, z,
        x2, y2, z,
        x2, y, z,

        x2, y, z2,
        x2, y2, z2,
        x, y2, z2,
        x, y, z2,

        x2, y, z2,
        x, y, z2,
        x, y, z,
        x2, y, z,

        x2, y2, z,
        x, y2, z,
        x, y2, z2,
        x2, y2, z2,

        x, y2, z2,
        x, y2, z,
        x, y, z,
        x, y, z2,

        x2, y, z2,
        x2, y, z,
        x2, y2, z,
        x2, y2, z2,
    ), dtype=np.float32)

    if textureVertices is None:
        textureVertices = np.array([
        [
        [0, -dy * 16,],
        [0, 0,],
        [dx * 16, 0,],
        [dx * 16, -dy * 16,],
        ],

        [
        [dx * 16, -dy * 16,],
        [dx * 16, 0,],
        [0, 0,],
        [0, -dy * 16,],
        ],

        [
        [dx * 16, -dz * 16,],
        [0, -dz * 16,],
        [0, 0,],
        [dx * 16, 0,],
        ],

        [
        [dx * 16, 0,],
        [0, 0,],
        [0, -dz * 16,],
        [dx * 16, -dz * 16,],
        ],

        [
        [dz * 16, 0,],
        [0, 0,],
        [0, -dy * 16,],
        [dz * 16, -dy * 16,],
        ],

        [
        [dz * 16, -dy * 16,],
        [0, -dy * 16,],
        [0, 0,],
        [dz * 16, 0,],
        ]

        ], dtype=np.float32)

        if selectionBox:
            textureVertices[0:2] += (16 * (x & 15), 16 * (y2 & 15))
            textureVertices[2:4] += (16 * (x & 15), -16 * (z & 15))
            textureVertices[4:6] += (16 * (z & 15), 16 * (y2 & 15))
            textureVertices[:] += 0.5

    GL.glVertexPointer(3, GL.GL_FLOAT, 0, cubeVertices)
    if texture != None:
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        texture.bind()
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, textureVertices),

    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glEnable(GL.GL_POLYGON_OFFSET_LINE)

    GL.glDrawArrays(cubeType, 0, 24)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glDisable(GL.GL_POLYGON_OFFSET_LINE)

    if texture != None:
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)


def drawTerrainCuttingWire(box,
                           c0=(0.75, 0.75, 0.75, 0.4),
                           c1=(1.0, 1.0, 1.0, 1.0)):

    # glDepthMask(False)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glColor(*c1)
    GL.glLineWidth(2.0)
    drawCube(box, cubeType=GL.GL_LINE_STRIP)

    GL.glDepthFunc(GL.GL_GREATER)
    GL.glColor(*c0)
    GL.glLineWidth(1.0)
    drawCube(box, cubeType=GL.GL_LINE_STRIP)

    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glDisable(GL.GL_DEPTH_TEST)


def loadTerrainTexture():
    pngFile = None

    texW, texH, terrain_data = loadPNGFile("terrain.png")

    def slurpZipExt(zipextfile):
        # zipextfile.read() doesn't read all available data
        all_data = ""
        data = zipextfile.read()
        while len(data):
            all_data += data
            data = zipextfile.read()
        return BytesIO(all_data)

    if pngFile is not None:
        try:
            texW, texH, terrain_data = loadPNGData(slurpZipExt(pngFile))

        except Exception as e:
            traceback.print_exc()
            print(repr(e), "while loading texture pack")


    from renderer import LeafBlockRenderer
    from renderer import GenericBlockRenderer
    LeafBlockRenderer.leafColor = LeafBlockRenderer.leafColorDefault
    GenericBlockRenderer.grassColor = GenericBlockRenderer.grassColorDefault

    def _loadFunc():
        loadTextureFunc(texW, texH, terrain_data)

    tex = glutils.Texture(_loadFunc)
    tex.data = terrain_data
    return tex


def loadPNGData(filename):
    # Load image and convert to rgba
    image = Image.open(directories.ASSETS / filename).convert("RGBA")
    # Convert the data to a np array
    data = np.array(image)
    # Extract the weight and width from the shape
    h, w = data.shape[:2]

    # Return final data
    return w, h, data


def loadPNGFile(filename):
    (w, h, data) = loadPNGData(filename)
    return w, h, data


def loadTextureFunc(w, h, n_data):
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w, h, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, n_data)
    return w, h


def loadPNGTexture(filename):
    try:
        w, h, n_data = loadPNGFile(filename)

        tex = glutils.Texture(functools.partial(loadTextureFunc, w, h, n_data))
        tex.data = n_data
        return tex
    except Exception as e:
        print("Exception loading ", filename, ": ", repr(e))
        return glutils.Texture()


import glutils


def normalize(x):
    l = x[0] * x[0] + x[1] * x[1] + x[2] * x[2]
    if l <= 0.0:
        return [0, 0, 0]
    size = np.sqrt(l)
    if size <= 0.0:
        return [0, 0, 0]
    return [a / size for a in x]


def normalize_size(x):
    l = x[0] * x[0] + x[1] * x[1] + x[2] * x[2]
    if l <= 0.0:
        return [0., 0., 0.], 0.
    size = np.sqrt(l)
    if size <= 0.0:
        return [0, 0, 0], 0
    return (x / size), size


# Label = GLLabel

class HotkeyColumn(Widget):
    is_gl_container = True

    def __init__(self, items, keysColumn=None, buttonsColumn=None):
        if keysColumn is None:
            keysColumn = []
        if buttonsColumn is None:
            buttonsColumn = []

        Widget.__init__(self)
        for (hotkey, title, action) in items:
            if isinstance(title, str):
                button = Button(title, action=action)
            else:
                button = ValueButton(ref=title, action=action, width=200)
            button.anchor = self.anchor

            label = Label(hotkey, width=75, margin=button.margin)
            label.anchor = "wh"

            label.height = button.height

            keysColumn.append(label)
            buttonsColumn.append(button)

        self.buttons = list(buttonsColumn)

        buttonsColumn = Column(buttonsColumn)
        buttonsColumn.anchor = self.anchor
        keysColumn = Column(keysColumn)

        commandRow = Row((keysColumn, buttonsColumn))
        self.add(commandRow)
        self.shrink_wrap()


from albow import CheckBox, AttrRef, Menu


class MenuButton(Button):
    def __init__(self, title, choices, **kw):
        Button.__init__(self, title, **kw)
        self.choices = choices
        self.menu = Menu(title, ((c, c) for c in choices))

    def action(self):
        index = self.menu.present(self, (0, 0))
        if index == -1:
            return
        self.menu_picked(index)

    def menu_picked(self, index):
        pass


class ChoiceButton(ValueButton):
    align = "c"
    choose = None

    def __init__(self, choices, **kw):
        # passing an empty list of choices is ill-advised

        if 'choose' in kw:
            self.choose = kw.pop('choose')

        ValueButton.__init__(self, action=self.showMenu, **kw)

        self.choices = choices or ["[UNDEFINED]"]

        widths = [self.font.size(c)[0] for c in choices] + [self.width]
        if len(widths):
            self.width = max(widths) + self.margin * 2

        self.choiceIndex = 0

    def showMenu(self):
        choiceIndex = self.menu.present(self, (0, 0))
        if choiceIndex != -1:
            self.choiceIndex = choiceIndex
            if self.choose:
                self.choose()

    def get_value(self):
        return self.selectedChoice

    @property
    def selectedChoice(self):
        if self.choiceIndex >= len(self.choices) or self.choiceIndex < 0:
            return ""
        return self.choices[self.choiceIndex]

    @selectedChoice.setter
    def selectedChoice(self, val):
        idx = self.choices.index(val)
        if idx != -1:
            self.choiceIndex = idx

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(self, ch):
        self._choices = ch
        self.menu = Menu("", ((name, "pickMenu") for name in self._choices))


def CheckBoxLabel(title, *args, **kw):
    tooltipText = kw.pop('tooltipText', None)

    cb = CheckBox(*args, **kw)
    lab = Label(title, fg_color=cb.fg_color)
    lab.mouse_down = cb.mouse_down

    if tooltipText:
        cb.tooltipText = tooltipText
        lab.tooltipText = tooltipText

    class CBRow(Row):
        margin = 0

        @property
        def value(self):
            return self.checkbox.value

        @value.setter
        def value(self, val):
            self.checkbox.value = val

    row = CBRow((lab, cb))
    row.checkbox = cb
    return row


def FloatInputRow(title, *args, **kw):
    return Row((Label(title, tooltipText=kw.get('tooltipText')), FloatField(*args, **kw)))


def IntInputRow(title, *args, **kw):
    return Row((Label(title, tooltipText=kw.get('tooltipText')), IntField(*args, **kw)))

def TextInputRow(title, *args, **kw):
    return Row((Label(title, tooltipText=kw.get('tooltipText')), TextField(*args, **kw)))

from albow.dialogs import Dialog
from datetime import timedelta


def setWindowCaption(prefix):
    caption = display.get_caption()[0]

    class ctx:
        def __enter__(self):
            display.set_caption(prefix + caption)

        def __exit__(self, *args):
            display.set_caption(caption)
    return ctx()


def showProgress(progressText, progressIterator, cancel=False):
    """Show the progress for a long-running synchronous operation.
    progressIterator should be a generator-like object that can return
    either None, for an indeterminate indicator,
    A float value between 0.0 and 1.0 for a determinate indicator,
    A string, to update the progress info label
    or a tuple of (float value, string) to set the progress and update the label"""
    class ProgressWidget(Dialog):
        progressFraction = 0.0
        firstDraw = False

        def draw(self, surface):
            Widget.draw(self, surface)
            frameStart = datetime.now()
            frameInterval = timedelta(0, 1, 0) / 2
            amount = None

            try:
                while datetime.now() < frameStart + frameInterval:
                    amount = next(progressIterator)
                    if self.firstDraw is False:
                        self.firstDraw = True
                        break

            except StopIteration:
                self.dismiss()

            infoText = ""
            if amount is not None:

                if isinstance(amount, tuple):
                    if len(amount) > 2:
                        infoText = ": " + amount[2]

                    amount, max = amount[:2]

                else:
                    max = amount
                maxwidth = (self.width - self.margin * 2)
                if amount is None:
                    self.progressBar.width = maxwidth
                    self.progressBar.bg_color = (255, 255, 25, 255)
                elif isinstance(amount, str):
                    self.statusText = amount
                else:
                    self.progressAmount = amount
                    if isinstance(amount, (int, float)):
                        self.progressFraction = float(amount) / (float(max) or 1)
                        self.progressBar.width = maxwidth * self.progressFraction
                        self.statusText = str("{0} / {1}".format(amount, max))
                    else:
                        self.statusText = str(amount)

                if infoText:
                    self.statusText += infoText

        @property
        def estimateText(self):
            delta = ((datetime.now() - self.startTime))
            progressPercent = (int(self.progressFraction * 10000))
            left = delta * (10000 - progressPercent) / (progressPercent or 1)
            return "Time left: {0}".format(left)

        def cancel(self):
            if cancel:
                self.dismiss(False)

        def idle_event(self, evt):
            self.invalidate()

    widget = ProgressWidget()
    widget.progressText = progressText
    widget.statusText = ""
    widget.progressAmount = 0.0

    progressLabel = ValueDisplay(ref=AttrRef(widget, 'progressText'), width=550)
    statusLabel = ValueDisplay(ref=AttrRef(widget, 'statusText'), width=550)
    estimateLabel = ValueDisplay(ref=AttrRef(widget, 'estimateText'), width=550)

    progressBar = Widget(size=(550, 20), bg_color=(150, 150, 150, 255))
    widget.progressBar = progressBar
    col = (progressLabel, statusLabel, estimateLabel, progressBar)
    if cancel:
        cancelButton = Button("Cancel", action=widget.cancel, fg_color=(255, 0, 0, 255))
        col += (Column((cancelButton,), align="r"),)

    widget.add(Column(col))
    widget.shrink_wrap()
    widget.startTime = datetime.now()
    if widget.present():
        return widget.progressAmount
    else:
        return "Canceled"

from glutils import DisplayList

import functools
