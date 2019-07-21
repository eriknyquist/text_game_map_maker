import os
import sys
import json
import zlib

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_maker.tile import tile
from text_game_maker.player import player
from text_game_maker.game_objects.base import serialize, deserialize
from text_game_maker.game_objects import __object_model_version__ as obj_version

from qt_auto_form import QtAutoForm

_tiles = {}

tile_border_pixels = 4
start_tile_colour = '#6bfa75'
tile_border_colour = '#000000'
selected_border_colour = '#ff0000'
door_colour = QtCore.Qt.black
keypad_door_colour = QtCore.Qt.blue

button_style = "border:4px solid %s; background-color: None" % tile_border_colour
start_button_style = "border:4px solid %s; background-color: %s" % (tile_border_colour, start_tile_colour)

_move_map = {
    'north': (-1, 0),
    'south': (1, 0),
    'east': (0, 1),
    'west': (0, -1),
}

def position_handler(tileobj, pos):
    print(tileobj.tile_id, pos)

def getTilePositions(start_tile, callback):
    positions = {}
    seen = []
    pos = (0, 0)
    tilestack = [(start_tile, None, None)]

    while tilestack:
        curr, newpos, movedir = tilestack.pop(0)
        if newpos is not None:
            pos = newpos

        if curr in seen:
            continue

        seen.append(curr)

        if movedir is not None:
            xinc, yinc = _move_map[movedir]
            oldx, oldy = pos
            newx, newy = oldx + xinc, oldy + yinc
            pos = (newx, newy)

        if curr.is_door():
            curr = curr.replacement_tile

        positions[curr.tile_id] = pos

        for direction in _move_map:
            n = getattr(curr, direction)
            if n:
                tilestack.append((n, pos, direction))

    return positions

def _set_button_style(button, selected=False, start=False, filled=True):
    colour = "background-color: None"
    border = ""

    if selected:
        border = "border:%dpx solid %s" % (tile_border_pixels, selected_border_colour)
    elif filled:
        border = "border:%dpx solid %s" % (tile_border_pixels, tile_border_colour)

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
        super(Button, self).paintEvent(event)

        for direction in self.doors:
            self.draw_door(door_colour, direction)

        for direction in self.keypad_doors:
            self.draw_door(keypad_door_colour, direction)

    def draw_door(self, colour, direction):
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()
        borderdelta = tile_border_pixels * 2

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

class TileSettings(object):
    spec = {
        'description': {'type':'long_str'},
        'name': {'type': 'str'},
        'tile_id': {'type': 'str', 'label': 'tile ID'},
        'first_visit_message': {'type': 'long_str', 'label': 'first visit message'},
        'first_visit_message_in_dark': {'type': 'bool', 'label': 'show first visit message if dark'},
        'dark': 'bool',
        'smell_description': {'type': 'str', 'label': 'smell description'},
        'ground_smell_description': {'type': 'str', 'label': 'ground smell description'},
        'ground_taste_description': {'type': 'str', 'label': 'ground taste description'}
    }

    def __init__(self):
        self.description = ""
        self.name = ""
        self.tile_id = ""
        self.first_visit_message = ""
        self.first_visit_message_in_dark = True
        self.dark = False
        self.smell_description = ""
        self.ground_smell_description = ""
        self.ground_taste_description = ""

class MapEditorWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MapEditorWindow, self).__init__(parent=parent)
        self.door_id = 1
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
                btn = Button(self)
                btn.setAttribute(QtCore.Qt.WA_StyledBackground)
                btn.setFixedSize(100, 100)
                btn.installEventFilter(btn)
                self.gridLayout.addWidget(btn, i, j)

        # Set up shortcuts for arrow keys
        QtWidgets.QShortcut(QtGui.QKeySequence("right"), self, self.rightKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("left"), self, self.leftKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("up"), self, self.upKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("down"), self, self.downKeyPress)

        # Set initial selection position
        button = self.gridLayout.itemAtPosition(0, 0).widget()
        self.setSelectedPosition(button)

    def moveSelection(self, y_move, x_move):
        if self.selectedPosition is None:
            return

        y, x = self.selectedPosition
        newpos = (y + y_move, x + x_move)

        if (newpos[0] < 0) or newpos[1] < 0:
            return

        button = self.gridLayout.itemAtPosition(*newpos).widget()
        self.setSelectedPosition(button)

    def leftKeyPress(self):
        self.moveSelection(*_move_map['west'])

    def rightKeyPress(self):
        self.moveSelection(*_move_map['east'])

    def upKeyPress(self):
        self.moveSelection(*_move_map['north'])

    def downKeyPress(self):
        self.moveSelection(*_move_map['south'])

    def buildToolbar(self):
        self.deleteButton = QtWidgets.QPushButton()
        self.doorButton = QtWidgets.QPushButton()
        self.keypadDoorButton = QtWidgets.QPushButton()
        self.saveButton = QtWidgets.QPushButton()
        self.loadButton = QtWidgets.QPushButton()
        self.loadFromSavedGameButton = QtWidgets.QPushButton()

        self.deleteButton.setText("Delete tile")
        self.doorButton.setText("Add door")
        self.keypadDoorButton.setText("Add door with keypad")
        self.saveButton.setText("Save to file")
        self.loadButton.setText("Load from file")
        self.loadFromSavedGameButton.setText("Load map from saved game")

        self.deleteButton.clicked.connect(self.deleteButtonClicked)
        self.doorButton.clicked.connect(self.doorButtonClicked)
        self.keypadDoorButton.clicked.connect(self.keypadDoorButtonClicked)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.loadButton.clicked.connect(self.loadButtonClicked)
        self.loadFromSavedGameButton.clicked.connect(self.loadFromSavedGameButtonClicked)

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
        self.deleteButton.setEnabled(False)

        tileButtonLayout = QtWidgets.QHBoxLayout()
        tileButtonLayout.addWidget(self.deleteButton)
        tileButtonLayout.addWidget(self.doorButton)
        tileButtonLayout.addWidget(self.keypadDoorButton)
        tileButtonLayout.addLayout(checkBoxLayout)
        tileButtonGroup = QtWidgets.QGroupBox("Edit selected tile")
        tileButtonGroup.setLayout(tileButtonLayout)

        self.buttonAreaLayout.addWidget(tileButtonGroup)
        self.buttonAreaLayout.addWidget(self.saveButton)
        self.buttonAreaLayout.addWidget(self.loadButton)
        self.buttonAreaLayout.addWidget(self.loadFromSavedGameButton)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            reply = self.yesNoDialog("Are you sure?", "Are you sure you want to quit?")
            if reply:
                self.close()

    def clearGrid(self):
        for pos in _tiles:
            button = self.gridLayout.itemAtPosition(*pos).widget()
            button.setText("")
            _set_button_style(button, selected=False, start=False, filled=False)

    def yesNoDialog(self, header="", msg="Are you sure?"):
        reply = QtWidgets.QMessageBox.question(self, header, msg,
                                               (QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Cancel),
                                               QtWidgets.QMessageBox.Cancel)

        return reply == QtWidgets.QMessageBox.Yes

    def errorDialog(self, heading="Error", message="Unrecoverable error occurred"):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(heading)
        msg.setInformativeText(message)
        msg.setWindowTitle("Critical error!")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def serialize(self):
        attrs = {}
        start_tile = _tiles[self.startTilePosition]

        attrs['tile_list'] = tile.crawler(start_tile)
        attrs['start_tile'] = start_tile.tile_id
        attrs['positions'] = {_tiles[pos].tile_id: list(pos) for pos in _tiles}

        return attrs

    def drawTileMap(self, start_tile, positions):
        for tile_id in positions:
            pos = tuple(positions[tile_id])
            tileobj = tile.get_tile_by_id(tile_id)
            if tileobj is None:
                continue

            _tiles[pos] = tileobj
            button = self.gridLayout.itemAtPosition(*pos).widget()
            button.setText(tileobj.tile_id)

            is_start = tileobj is start_tile
            _set_button_style(button, selected=False, start=is_start, filled=True)
            self.redrawDoors(button, tileobj)

    def deserialize(self, attrs):
        start_tile = tile.builder(attrs['tile_list'], attrs['start_tile'], obj_version)

        self.clearGrid()
        _tiles.clear()
        self.drawTileMap(start_tile, attrs['positions'])
        self.startTilePosition = tuple(attrs['positions'][start_tile.tile_id])

    def deserializeFromSaveFile(self, attrs):
        if (player.TILES_KEY not in attrs) or (player.START_TILE_KEY not in attrs):
            return False

        # Remove items, people and events, we're not dealing with them here
        tilelist = attrs[player.TILES_KEY]
        for tiledata in tilelist:
            for loc in tiledata['items']:
                tiledata['items'][loc] = []

            for loc in tiledata['people']:
                tiledata['people'][loc] = []

            del tiledata['enter_event']
            del tiledata['exit_event']

        # build tilemap from list of tile data
        start_tile_name = attrs[player.START_TILE_KEY]
        start_tile = tile.builder(tilelist, start_tile_name, obj_version)

        # find lowest index tile in tilemap
        positions = getTilePositions(start_tile, position_handler)
        lowest_y = positions[start_tile.tile_id][0]
        lowest_x = positions[start_tile.tile_id][1]

        for tile_id in positions:
            pos = positions[tile_id]
            if (pos[0] < lowest_y):
                lowest_y = pos[0]

            if (pos[1] < lowest_x):
                lowest_x = pos[1]

        # Correct tile positions so lowest tile is (0, 0)
        for tile_id in positions:
            old = positions[tile_id]
            positions[tile_id] = (old[0] + abs(lowest_y), old[1] + abs(lowest_x))

        self.clearGrid()
        _tiles.clear()
        self.drawTileMap(start_tile, positions)
        self.startTilePosition = positions[start_tile.tile_id]

        return True

    def closestTileToOrigin(self, tilemap):
        seen = []
        pos = (0, 0)
        lowest_tile = start_tile
        lowest_tile_pos = (0, 0)
        tilestack = [(start_tile, None, None)]

        while tilestack:
            curr, newpos, movedir = tilestack.pop(0)
            if newpos is not None:
                pos = newpos

            if curr in seen:
                continue

            seen.append(curr)

            if movedir is not None:
                xinc, yinc = _move_map[movedir]
                oldx, oldy = pos
                newx, newy = oldx + xinc, oldy + yinc
                pos = (newx, newy)

                lowestx, lowesty = lowest_tile_pos
                if (newx <= lowestx) and (newy <= lowesty):
                    lowest_tile_pos = pos
                    lowest_tile = curr

            for direction in _move_map:
                n = getattr(curr, direction)
                if n:
                    tilestack.append((n, pos, direction))

            return lowest_tile

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

    def tileIDExists(self, tile_id):
        val = tile.get_tile_by_id(tile_id)
        return val is not None

    def getDoorSettings(self, settings_obj, window_title):
        complete = False
        settings_obj.tile_id = "door%d" % self.door_id
        self.door_id += 1

        while not complete:
            dialog = QtAutoForm(settings_obj, title=window_title, spec=settings_obj.spec)
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()

            # Dialog was cancelled, we're done
            if not dialog.wasAccepted():
                return False

            if str(settings_obj.tile_id).strip() == '':
                self.errorDialog("Invalid tile ID", "tile ID field cannot be empty")
            elif self.tileIDExists(settings_obj.tile_id):
                self.errorDialog("Unable to create door",
                                 "Tile ID '%s' is already is use!" % settings_obj.tile_id)
            else:
                complete = True

        return True

    def oppositeDoorExists(self, opposite_tile, direction):
        if not opposite_tile:
            return False

        opposite_dir = tile.reverse_direction(direction)
        opposite = getattr(opposite_tile, opposite_dir)
        return opposite and opposite.is_door()

    def loadFromSavedGameButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getOpenFileName(self, "QFileDialog.getOpenFileName()",
                             "", "All Files (*);;Text Files (*.txt)",
                                                 options=options)

        if filename.strip() == '':
            return

        if not os.path.exists(filename):
            self.errorDialog("Error opening file", "Unable to open file '%s'" % filename)
            return

        try:
            with open(filename, 'rb') as fh:
                data = fh.read()
                strdata = zlib.decompress(data).decode("utf-8")
                attrs = json.loads(strdata)
        except Exception as e:
            self.errorDialog("Error loading saved game state",
                             "Unable to load saved game data from file %s: %s"
                             % (filename, str(e)))
            return

        self.deserializeFromSaveFile(attrs)

    def deleteButtonClicked(self):
        if self.selectedPosition not in _tiles:
            self.errorDialog("Unable to delete tile", "No tile in this space "
                             "to delete")
            return

        tileobj = _tiles[self.selectedPosition]
        button = self.gridLayout.itemAtPosition(*self.selectedPosition).widget()

        reply = self.yesNoDialog("Are you sure?", "Are you sure you want to "
                                "delete this tile (tile ID is '%s')" % (tileobj.tile_id))
        if not reply:
            return

        self.disconnectSurroundingTiles(tileobj, self.selectedPosition)
        del _tiles[self.selectedPosition]
        button.setText("")

        if self.startTilePosition == self.selectedPosition:
            self.startTilePosition = None

        _set_button_style(button, selected=False, start=False, filled=False)
        self.redrawDoors(button, None)

    def doorButtonClicked(self):
        settings = DoorSettings()
        wasAccepted = self.getDoorSettings(settings, "Door settings")
        if not wasAccepted:
            return

        tileobj = _tiles[self.selectedPosition]
        button = self.gridLayout.itemAtPosition(*self.selectedPosition).widget()

        replace = getattr(tileobj, settings.direction)

        # Check if there's already a door in this direction on the adjacent tile
        if self.oppositeDoorExists(replace, settings.direction):
            self.errorDialog("Unable to add door", "There is an existing door "
                             " locked from the opposite direction (tile ID '%s')"
                             % replace.tile_id)
            return

        door = tile.LockedDoor(settings.prefix, settings.name, tileobj, replace)
        door.set_tile_id(settings.tile_id)
        setattr(tileobj, settings.direction, door)

        button.add_doors(doors=[settings.direction])

    def keypadDoorButtonClicked(self):
        settings = KeypadDoorSettings()
        wasAccepted = self.getDoorSettings(settings, "Keypad door settings")
        if not wasAccepted:
            return

        tileobj = _tiles[self.selectedPosition]
        button = self.gridLayout.itemAtPosition(*self.selectedPosition).widget()

        replace = getattr(tileobj, settings.direction)

        # Check if there's already a door in this direction on the adjacent tile
        if self.oppositeDoorExists(replace, settings.direction):
            self.errorDialog("Unable to add door", "There is an existing door "
                             " locked from the opposite direction (tile ID '%s')"
                             % replace.tile_id)
            return

        door = tile.LockedDoorWithKeypad(settings.code, prefix=settings.prefix,
                                         name=settings.name, src_tile=tileobj,
                                         replacement_tile=replace)

        door.set_tile_id(settings.tile_id)
        door.set_prompt(settings.prompt)
        setattr(tileobj, settings.direction, door)

        button.add_doors(keypad_doors=[settings.direction])

    def redrawDoors(self, button, tileobj):
        doors = []
        keypad_doors = []

        if tileobj is not None:
            for direction in ['north', 'south', 'east', 'west']:
                attr = getattr(tileobj, direction)
                if type(attr) is tile.LockedDoor:
                    doors.append(direction)
                elif type(attr) == tile.LockedDoorWithKeypad:
                    keypad_doors.append(direction)

        button.doors = []
        button.keypad_doors = []
        button.add_doors(doors, keypad_doors)

    def saveButtonClicked(self):
        if self.startTilePosition is None:
            self.errorDialog("Unable to save map", "No start tile is set. You "
                             "must set a start tile before saving.")
            return

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

        if filename.strip() == '':
            return

        if not os.path.exists(filename):
            self.errorDialog("Error opening file", "Unable to open file '%s'" % filename)
            return

        try:
            with open(filename, 'r') as fh:
                attrs = json.load(fh)

            self.deserialize(attrs)
        except Exception as e:
            self.errorDialog("Error loading saved map data",
                             "Unable to load saved map data from file %s: %s"
                             % (filename, str(e)))

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

        for obj in [self.doorButton, self.keypadDoorButton, self.deleteButton]:
            if obj.isEnabled() != filled:
                obj.setEnabled(filled)

        button.setFocus(True)

    def onMiddleClick(self, button):
        pass

    def onRightClick(self, button):
        self.setSelectedPosition(button)

    def runTileBuilderDialog(self, position):
        settings = TileSettings()

        if position in _tiles:
            tileobj = _tiles[position]
            settings.description = tileobj.description
            settings.name = tileobj.name
            settings.tile_id = tileobj.tile_id
            settings.first_visit_message = tileobj.first_visit_message
            settings.first_visit_message_in_dark = tileobj.first_visit_message_in_dark
            settings.dark = tileobj.dark
            settings.smell_description = tileobj.smell_description
            settings.ground_smell_description = tileobj.ground_smell_description
            settings.ground_taste_description = tileobj.ground_taste_description
        else:
            tileobj = tile.Tile()
            settings.tile_id = "tile%d" % tile.Tile.tile_id

        complete = False
        while not complete:
            dialog = QtAutoForm(settings, title="Tile attributes", spec=settings.spec)
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()

            if not dialog.wasAccepted():
                return None

            if str(settings.tile_id).strip() == '':
                self.errorDialog("Invalid tile ID", "tile ID field cannot be empty")
            elif (tileobj.tile_id != settings.tile_id) and self.tileIDExists(settings.tile_id):
                self.errorDialog("Unable to create tile", "Tile ID '%s' already in use!"
                                 % settings.tile_id)
            else:
                complete = True

        if settings.tile_id != tileobj.tile_id:
            tileobj.set_tile_id(settings.tile_id)

        tileobj.description = settings.description
        tileobj.name = settings.name
        tileobj.first_visit_message = settings.first_visit_message
        tileobj.first_visit_message_in_dark = settings.first_visit_message_in_dark
        tileobj.dark = settings.dark
        tileobj.smell_description = settings.smell_description
        tileobj.ground_smell_description = settings.ground_smell_description
        tileobj.ground_taste_description = settings.ground_taste_description

        return tileobj

    def disconnectSurroundingTiles(self, tileobj, position):
        north, south, east, west = self.surroundingTiles(position)
        adjacent_tiles = {'north': north, 'south': south, 'east': east, 'west': west}

        for direction in adjacent_tiles:
            adjacent_tileobj = adjacent_tiles[direction]

            if not adjacent_tileobj:
                continue

            setattr(tileobj, direction, None)

            reverse_direction = tile.reverse_direction(direction)
            reverse_pointer = getattr(adjacent_tileobj, reverse_direction)

            if reverse_pointer and reverse_pointer.is_door():
                reverse_pointer.replacement_tile = None
            else:
                setattr(adjacent_tileobj, tile.reverse_direction(direction), None)

    def connectSurroundingTiles(self, tileobj, position):
        north, south, east, west = self.surroundingTiles(position)
        adjacent_tiles = {'north': north, 'south': south, 'east': east, 'west': west}

        for direction in adjacent_tiles:
            adjacent_tileobj = adjacent_tiles[direction]

            if not adjacent_tileobj:
                continue

            setattr(tileobj, direction, adjacent_tileobj)

            reverse_direction = tile.reverse_direction(direction)
            reverse_pointer = getattr(adjacent_tileobj, reverse_direction)

            if reverse_pointer and reverse_pointer.is_door():
                reverse_pointer.replacement_tile = tileobj
            else:
                setattr(adjacent_tileobj, tile.reverse_direction(direction), tileobj)

    def onLeftClick(self, button):
        position = self.getButtonPosition(button)
        tileobj = self.runTileBuilderDialog(position)

        # Dialog was cancelled or otherwise failed, we're done
        if tileobj is None:
            self.setSelectedPosition(button)
            return

        if position not in _tiles:
            # Created a new tile
            _tiles[position] = tileobj
            _set_button_style(button, selected=True, start=False, filled=True)
            self.connectSurroundingTiles(tileobj, position)

        button.setText(str(tileobj.tile_id))
        self.setSelectedPosition(button)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MapEditorWindow()
    w.show()
    sys.exit(app.exec_())

