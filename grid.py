import sys
from PyQt5 import QtWidgets, QtCore

from text_game_maker.tile.tile import Tile
from text_game_maker.game_objects.base import serialize, deserialize
from text_game_maker.game_objects import __object_model_version__ as obj_version

from qt_auto_form import QtAutoForm

_tiles = {}

class IndicSelectWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(IndicSelectWindow, self).__init__(parent=parent)
        self.resize(500, 400)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)
        self.selectedTile = None

        for i in range(100):
            for j in range(100):
                btn = QtWidgets.QPushButton()
                btn.setFixedSize(100, 100)
                btn.installEventFilter(self)
                self.gridLayout.addWidget(btn, i, j)

    def getButtonPosition(self, button):
        idx = self.gridLayout.indexOf(button)
        return self.gridLayout.getItemPosition(idx)[:2]

    def surroundingTiles(self, position):
        def _fetch_tile(pos, yoff, xoff):
            oldy, oldx = pos
            newy = oldy + yoff
            newx = oldx + xoff

            if newy < 0: return None
            if newx < 0: return None

            newpos = (newy, newx)
            if newpos not in _tiles:
                return None

            return _tiles[newpos]

        north = _fetch_tile(position, -1, 0)
        south = _fetch_tile(position, 1, 0)
        east = _fetch_tile(position, 0, 1)
        west = _fetch_tile(position, 0, -1)

        return north, south, east, west

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.onLeftClick(obj)
            elif event.button() == QtCore.Qt.RightButton:
                self.onRightClick(obj)
            elif event.button() == QtCore.Qt.MiddleButton:
                self.onMiddleClick(obj)

        return QtCore.QObject.event(obj, event)

    def onMiddleClick(self, button):
        pass

    def onRightClick(self, button):
        self.selectedTile = self.getButtonPosition(button)

    def onLeftClick(self, button):
        position = self.getButtonPosition(button)

        if position in _tiles:
            tile = _tiles[position]
        else:
            tile = Tile()

        spec = {
            'description': 'str',
            'name': 'str',
            'tile_id': 'str',
            'first_visit_message': 'str',
            'first_visit_message_in_dark': 'bool',
            'dark': 'bool',
            'smell_description': 'str',
            'ground_smell_description': 'str',
            'ground_taste_description': 'str'
        }

        dialog = QtAutoForm(tile, spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        self.selectedTile = position

        # Dialog was cancelled, we're done
        if not dialog.wasAccepted():
            return

        button.setText(str(tile.tile_id))
        _tiles[position] = tile

        # Connect tile to surrounding tiles
        north, south, east, west = self.surroundingTiles(position)
        if north:
            tile.north = north
            north.south = tile

        if south:
            tile.south = south
            south.north = tile

        if east:
            tile.east = east
            east.west = tile

        if west:
            tile.west = west
            west.east = tile

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = IndicSelectWindow()
    w.show()
    sys.exit(app.exec_())
