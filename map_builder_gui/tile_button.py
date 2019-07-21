from PyQt5 import QtWidgets, QtCore, QtGui

import map_editor

door_colour = QtCore.Qt.black
keypad_door_colour = QtCore.Qt.blue

class TileButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(TileButton, self).__init__(parent)
        self.doors = []
        self.keypad_doors = []
        self.main = parent

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

    def add_doors(self, doors=[], keypad_doors=[]):
        self.doors.extend(doors)
        self.keypad_doors.extend(keypad_doors)
        self.update()

    def paintEvent(self, event):
        super(TileButton, self).paintEvent(event)

        for direction in self.doors:
            self.draw_door(door_colour, direction)

        for direction in self.keypad_doors:
            self.draw_door(keypad_door_colour, direction)

    def draw_door(self, colour, direction):
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()
        borderdelta = map_editor.tile_border_pixels * 2

        qwidth = (width - borderdelta) / 4.0
        qheight = (height - borderdelta) / 4.0

        adjusted_qheight = qheight + borderdelta
        adjusted_qwidth = qwidth + borderdelta

        if direction == "north":
            points = (adjusted_qheight, 0, height - adjusted_qheight, 0)
        elif direction == "south":
            points = (adjusted_qheight, width, height - adjusted_qheight, width)
        if direction == "east":
            points = (height, adjusted_qwidth, height, width - adjusted_qwidth)
        if direction == "west":
            points = (0, adjusted_qwidth, 0, width - adjusted_qwidth)

        self.draw_line(colour, qwidth, *points)

    def draw_line(self, colour, width, x1, y1, x2, y2):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(colour, width))
        brush = QtGui.QBrush()
        painter.setBrush(brush)
        painter.drawLine(QtCore.QLine(x1, y1, x2, y2))

