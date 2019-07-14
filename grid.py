import sys
import json

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_maker.tile import tile
from text_game_maker.game_objects.base import serialize, deserialize
from text_game_maker.game_objects import __object_model_version__ as obj_version

from qt_auto_form import QtAutoForm

_tiles = {}

start_tile_colour = '#6bfa75'
tile_border_colour = '#000000'
selected_border_colour = '#ff0000'
door_colour = QtCore.Qt.blue
keypad_door_colour = QtCore.Qt.green

button_style = "border:4px solid %s; background-color: None" % tile_border_colour
start_button_style = "border:4px solid %s; background-color: %s" % (tile_border_colour, start_tile_colour)

def _set_button_style(button, selected=False, start=False, filled=True):
    colour = "background-color: None"
    border = ""

    if selected:
        border = "border:4px solid %s" % selected_border_colour
    elif filled:
        border = "border:4px solid %s" % tile_border_colour

    if start:
        colour = "background-color: %s" % start_tile_colour

    button.setStyleSheet(';'.join([border, colour]))

# Set checkbox state without triggering the stateChanged signal
def _silent_checkbox_set(checkbox, value, handler):
    checkbox.stateChanged.disconnect(handler)
    checkbox.setChecked(value)
    checkbox.stateChanged.connect(handler)

class Button(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(Button, self).__init__(parent)
        self.doors = []
        self.keypad_doors = []

    def draw_doors(self, doors=[], keypad_doors=[]):
        self.doors = doors
        self.keypad_doors = keypad_doors
        self.update()

    def paintEvent(self, event):
        super(Button, self).paintEvent(event)

        for direction in self.doors:
            self.draw_door(door_colour, direction)

        for direction in self.keypad_doors:
            self.draw_door(keypad_door_colour, direction)

    def draw_door(self, colour, direction):
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()

        qwidth = width / 4
        qheight = height / 4

        if direction == "north":
            points = (qheight, 0, height - qheight, 0)
        elif direction == "south":
            points = (qheight, width, height - qheight, width)
        if direction == "east":
            points = (height, qwidth, height, width - qwidth)
        if direction == "west":
            points = (0, qwidth, 0, width - qwidth)

        self.draw_line(colour, *points)

    def draw_line(self, colour, x1, y1, x2, y2):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(colour, self.frameGeometry().width() / 8))
        brush = QtGui.QBrush()
        painter.setBrush(brush)
        painter.drawLine(QtCore.QLine(x1, y1, x2, y2))

class DoorSettings(object):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"}
    }

    def __init__(self):
        self.prefix = ""
        self.name = ""
        self.direction = ""
        self.tile_id = ""

class KeypadDoorSettings(object):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"},
        "code": {"type": "int", "label": "keypad code"},
        "prompt": {"type": "str", "label": "keypad prompt"}
    }

    def __init__(self):
        self.prefix = ""
        self.name = ""
        self.direction = ""
        self.tile_id = ""
        self.code = 0
        self.prompt = ""

class MapEditorWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MapEditorWindow, self).__init__(parent=parent)
        self.resize(500, 400)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.gridAreaLayout = QtWidgets.QHBoxLayout()
        self.buttonAreaLayout = QtWidgets.QHBoxLayout()
        self.buildToolbar()

        # Build scrollable grid area
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridAreaLayout.addWidget(self.scrollArea)

        self.mainLayout.addLayout(self.buttonAreaLayout)
        self.mainLayout.addLayout(self.gridAreaLayout)
        self.selectedPosition = None
        self.startTilePosition = None

        self.rows = 100
        self.columns = 100

        for i in range(self.rows):
            for j in range(self.columns):
                btn = Button()
                btn.setAttribute(QtCore.Qt.WA_StyledBackground)
                btn.setFixedSize(100, 100)
                btn.installEventFilter(self)
                self.gridLayout.addWidget(btn, i, j)

    def buildToolbar(self):
        self.doorButton = QtWidgets.QPushButton()
        self.keypadDoorButton = QtWidgets.QPushButton()
        self.saveButton = QtWidgets.QPushButton()
        self.loadButton = QtWidgets.QPushButton()
        self.exportButton = QtWidgets.QPushButton()

        self.doorButton.setText("Add door")
        self.keypadDoorButton.setText("Add door with keypad")
        self.saveButton.setText("Save to file")
        self.loadButton.setText("Load from file")
        self.exportButton.setText("Export map")

        self.doorButton.clicked.connect(self.doorButtonClicked)
        self.keypadDoorButton.clicked.connect(self.keypadDoorButtonClicked)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.loadButton.clicked.connect(self.loadButtonClicked)
        self.exportButton.clicked.connect(self.exportButtonClicked)

        self.startTileCheckBox = QtWidgets.QCheckBox()
        self.startTileCheckBox.setStyleSheet("margin-left:50%; margin-right:50%;")
        self.startTileCheckBox.setChecked(False)
        self.startTileCheckBox.setEnabled(False)
        self.startTileCheckBox.stateChanged.connect(self.onStartTileSet)

        label = QtWidgets.QLabel("Start tile")
        label.setAlignment(QtCore.Qt.AlignCenter)
        checkBoxLayout = QtWidgets.QVBoxLayout()
        checkBoxLayout.addWidget(label)
        checkBoxLayout.addWidget(self.startTileCheckBox)
        checkBoxLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.doorButton.setEnabled(False)
        self.keypadDoorButton.setEnabled(False)

        tileButtonLayout = QtWidgets.QHBoxLayout()
        tileButtonLayout.addWidget(self.doorButton)
        tileButtonLayout.addWidget(self.keypadDoorButton)
        tileButtonLayout.addLayout(checkBoxLayout)
        tileButtonGroup = QtWidgets.QGroupBox("Edit selected tile")
        tileButtonGroup.setLayout(tileButtonLayout)

        self.buttonAreaLayout.addWidget(tileButtonGroup)
        self.buttonAreaLayout.addWidget(self.saveButton)
        self.buttonAreaLayout.addWidget(self.loadButton)

    def clearGrid(self):
        for pos in _tiles:
            button = self.gridLayout.itemAtPosition(*pos).widget()
            button.setText("")
            _set_button_style(button, selected=False, start=False, filled=False)

    def serialize(self):
        attrs = {}
        start_tile = _tiles[self.startTilePosition]

        attrs['tile_list'] = tile.crawler(start_tile)
        attrs['start_tile'] = start_tile.tile_id
        attrs['positions'] = {_tiles[pos].tile_id: list(pos) for pos in _tiles}

        return attrs

    def deserialize(self, attrs):
        start_tile = tile.builder(attrs['tile_list'], attrs['start_tile'], obj_version)

        _tiles.clear()
        self.clearGrid()

        for tile_id in attrs['positions']:
            pos = tuple(attrs['positions'][tile_id])
            tileobj = tile.get_tile_by_id(tile_id)
            if tileobj is None:
                continue

            _tiles[pos] = tileobj
            button = self.gridLayout.itemAtPosition(*pos).widget()
            button.setText(tileobj.tile_id)

            if tileobj is start_tile:
                _set_button_style(button, selected=False, start=True, filled=True)
            else:
                _set_button_style(button, selected=False, start=False, filled=True)

        self.startTilePosition = tuple(attrs['positions'][start_tile.tile_id])

    def onStartTileSet(self, state):
        if state == QtCore.Qt.Checked:
            if self.startTilePosition is not None:
                # Set current start tile colour back to default
                old_start = self.gridLayout.itemAtPosition(*self.startTilePosition).widget()
                _set_button_style(old_start, selected=False, start=False, filled=True)

            new_start = self.gridLayout.itemAtPosition(*self.selectedPosition).widget()
            _set_button_style(new_start, selected=True, start=True, filled=True)
            self.startTilePosition = self.selectedPosition
            self.startTileCheckBox.setEnabled(False)

    def doorButtonClicked(self):
        settings = DoorSettings()
        dialog = QtAutoForm(settings, title="Door settings", spec=settings.spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

        # Dialog was cancelled, we're done
        if not dialog.wasAccepted():
            return

    def keypadDoorButtonClicked(self):
        settings = KeypadDoorSettings()
        dialog = QtAutoForm(settings, title="Keypad door settings", spec=settings.spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

        # Dialog was cancelled, we're done
        if not dialog.wasAccepted():
            return

    def saveButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getSaveFileName(self, "QFileDialog.getSaveFileName()",
					         "", "All Files (*);;Text Files (*.txt)",
                                                 options=options)

        with open(filename, 'w') as fh:
            json.dump(self.serialize(), fh)

    def loadButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
       	options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getOpenFileName(self, "QFileDialog.getOpenFileName()",
					         "", "All Files (*);;Text Files (*.txt)",
                                                 options=options)

        with open(filename, 'r') as fh:
            attrs = json.load(fh)

        self.deserialize(attrs)

    def exportButtonClicked(self):
        pass

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

    def setSelectedPosition(self, button):
        if self.selectedPosition is not None:
            oldstart = self.selectedPosition == self.startTilePosition
            oldfilled = self.selectedPosition in _tiles
            oldbutton = self.gridLayout.itemAtPosition(*self.selectedPosition).widget()
            _set_button_style(oldbutton, selected=False, start=oldstart, filled=oldfilled)

        self.selectedPosition = self.getButtonPosition(button)

        newstart = self.selectedPosition == self.startTilePosition
        newfilled = self.selectedPosition in _tiles
        _set_button_style(button, selected=True, start=newstart, filled=newfilled)

        if self.selectedPosition == self.startTilePosition:
            _silent_checkbox_set(self.startTileCheckBox, True, self.onStartTileSet)
            self.startTileCheckBox.setEnabled(False)
        else:
            self.startTileCheckBox.setEnabled(True)
            _silent_checkbox_set(self.startTileCheckBox, False, self.onStartTileSet)

        filled = self.selectedPosition in _tiles

        if not filled:
            _silent_checkbox_set(self.startTileCheckBox, False, self.onStartTileSet)
            self.startTileCheckBox.setEnabled(False)


        for obj in [self.doorButton, self.keypadDoorButton]:
            if obj.isEnabled() != filled:
                obj.setEnabled(filled)

    def onMiddleClick(self, button):
        pass

    def onRightClick(self, button):
        self.setSelectedPosition(button)

    def onLeftClick(self, button):
        position = self.getButtonPosition(button)

        if position in _tiles:
            tileobj = _tiles[position]
        else:
            tileobj = tile.Tile()

        tilespec = {
            'description': {'type':'str'},
            'name': {'type': 'str'},
            'tile_id': {'type': 'str', 'label': 'tile ID'},
            'first_visit_message': {'type': 'str', 'label': 'first visit message'},
            'first_visit_message_in_dark': {'type': 'bool', 'label': 'show first visit message if dark'},
            'dark': 'bool',
            'smell_description': {'type': 'str', 'label': 'smell description'},
            'ground_smell_description': {'type': 'str', 'label': 'ground smell description'},
            'ground_taste_description': {'type': 'str', 'label': 'ground taste description'}
        }

        dialog = QtAutoForm(tileobj, title="Tile attributes", spec=tilespec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

        # Dialog was cancelled, we're done
        if not dialog.wasAccepted():
            self.setSelectedPosition(button)
            return

        if position not in _tiles:
            _set_button_style(button, selected=True, start=False, filled=True)

        button.setText(str(tileobj.tile_id))
        _tiles[position] = tileobj
        self.setSelectedPosition(button)

        # Connect tile to surrounding tiles
        north, south, east, west = self.surroundingTiles(position)
        if north:
            tileobj.north = north
            north.south = tileobj

        if south:
            tileobj.south = south
            south.north = tileobj

        if east:
            tileobj.east = east
            east.west = tileobj

        if west:
            tileobj.west = west
            west.east = tileobj

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MapEditorWindow()
    w.show()
    sys.exit(app.exec_())

