from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_maker.tile import tile

door_colour = QtCore.Qt.black
wall_colour = QtCore.Qt.black
selected_wall_colour = QtCore.Qt.red
keypad_door_colour = QtCore.Qt.blue

tile_border_pixels = 4
mask_tile_colour = '#858585'
start_tile_colour = '#6bfa75'
tile_border_colour = '#000000'
selected_border_colour = '#ff0000'

button_style = "border:4px solid %s; background-color: None" % tile_border_colour
start_button_style = "border:4px solid %s; background-color: %s" % (tile_border_colour, start_tile_colour)


class BorderType(object):
    SELECTED = 0
    FILLED = 1
    EMPTY = 2


class TileButton(QtWidgets.QPushButton):
    # Will be set by calculate_dimensions
    doorwidth = 0
    borderwidth = 0
    border_lines = []
    walls_map = {}
    doors_map = {}

    # When the cursor is hovering over a tile button, this will contain the
    # button object, otherwise None.
    hovering = None

    def __init__(self, parent=None):
        super(TileButton, self).__init__(parent)
        self.doors = []
        self.keypad_doors = []
        self.main = parent
        self.border_type = BorderType.EMPTY

    @classmethod
    def set_dimensions(cls, width, height):
        borderdelta = tile_border_pixels * 2

        qwidth = (width - borderdelta) / 4.0
        qheight = (height - borderdelta) / 4.0

        adjusted_qheight = qheight + borderdelta
        adjusted_qwidth = qwidth + borderdelta

        cls.doorwidth = qwidth
        cls.borderwidth = max(2, width / 16)

        cls.border_lines = [
            (0, width, 0, 0),
            (height, width, height, 0),
            (height, 0, 0, 0),
            (height, width, 0, width)
        ]

        cls.walls_map = {
            "north": (0, 0, height, 0),
            "south": (0, width, height, width),
            "east": (height, 0, height, width),
            "west": (0, 0, 0, width)
        }

        cls.doors_map = {
            "north": (adjusted_qheight, 0, height - adjusted_qheight, 0),
            "south": (adjusted_qheight, width, height - adjusted_qheight, width),
            "east": (height, adjusted_qwidth, height, width - adjusted_qwidth),
            "west": (0, adjusted_qwidth, 0, width - adjusted_qwidth)
        }

    def leaveEvent(self, event):
        self.__class__.hovering = None

    def enterEvent(self, event):
        self.__class__.hovering = self

        if self.main.tracking_tile_button_enter:
            self.main.onTileButtonEnter(self)

    def setStyle(self, selected=False, start=False, selection_mask=False):
        if selection_mask:
            colour = "background-color: %s" % mask_tile_colour
            self.setStyleSheet(colour)
        else:
            border = ""
            bordercolour = selected_wall_colour if selected else wall_colour

            if start:
                colour = "background-color: %s" % start_tile_colour
            else:
                colour = "background-color: None"

            self.setStyleSheet(colour)

            pos = self.main.getButtonPosition(self)
            tileobj = self.main.tileAtPosition(*pos)

            if selected:
                self.border_type = BorderType.SELECTED
            elif tileobj is None:
                self.border_type = BorderType.EMPTY
            else:
                self.border_type = BorderType.FILLED

        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.main.onLeftClick(obj)
            elif event.button() == QtCore.Qt.RightButton:
                self.main.onRightClick(obj)
            elif event.button() == QtCore.Qt.MiddleButton:
                self.main.onMiddleClick(obj)

        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
                self.main.onLeftClick(obj)

        return QtCore.QObject.event(obj, event)

    def clearDoors(self):
        self.doors = []
        self.keypad_doors = []
        self.update()

    def removeDoors(self, directions=[]):
        for d in directions:
            if d in self.doors:
                self.doors.remove(d)

            if d in self.keypad_doors:
                self.keypad_doors.remove(d)

    def addDoors(self, doors=[], keypad_doors=[]):
        self.doors.extend(doors)
        self.keypad_doors.extend(keypad_doors)

    def paintEvent(self, event):
        super(TileButton, self).paintEvent(event)

        for direction in self.doors:
            self.drawDoor(door_colour, direction)

        for direction in self.keypad_doors:
            self.drawDoor(keypad_door_colour, direction)

        if self.border_type == BorderType.SELECTED:
            self.drawBorder(selected_wall_colour)
        elif self.border_type == BorderType.FILLED:
            self.drawWalls()

    def drawBorder(self, colour):
        for points in self.border_lines:
            self.drawLine(colour, self.borderwidth, *points)

    def drawWalls(self):
        pos = self.main.getButtonPosition(self)
        tileobj = self.main.tileAtPosition(*pos)

        for direction in self.walls_map:
            adjacent = None
            if tileobj is not None:
                adjacent = getattr(tileobj, direction)

            if (adjacent is None) or adjacent.is_door():
                self.drawLine(wall_colour, self.borderwidth, *self.walls_map[direction])

    def drawDoor(self, colour, direction):
        points = self.doors_map[direction]
        self.drawLine(colour, self.doorwidth, *points)

    def redrawDoors(self):
        doors = []
        keypad_doors = []
        pos = self.main.getButtonPosition(self)
        tileobj = self.main.tileAtPosition(*pos)

        if tileobj is not None:
            for direction in ['north', 'south', 'east', 'west']:
                attr = getattr(tileobj, direction)
                if type(attr) is tile.LockedDoor:
                    doors.append(direction)
                elif type(attr) == tile.LockedDoorWithKeypad:
                    keypad_doors.append(direction)

        self.clearDoors()
        self.addDoors(doors, keypad_doors)
        self.update()

    def drawLine(self, colour, width, x1, y1, x2, y2):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(colour, width))
        brush = QtGui.QBrush()
        painter.setBrush(brush)
        painter.drawLine(QtCore.QLine(x1, y1, x2, y2))
