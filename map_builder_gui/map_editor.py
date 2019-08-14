import os
import json
import zlib

from PyQt5 import QtWidgets, QtCore, QtGui

import forms
from door_editor import DoorEditor
from tile_button import TileButton

from text_game_maker.tile import tile
from text_game_maker.player import player
from text_game_maker.game_objects.base import serialize, deserialize
from text_game_maker.game_objects import __object_model_version__ as obj_version

from qt_auto_form import QtAutoForm

_tiles = {}

_move_map = {
    'north': (-1, 0),
    'south': (1, 0),
    'east': (0, 1),
    'west': (0, -1)
}

def getTilePositions(start_tile):
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

# Set checkbox state without triggering the stateChanged signal
def _silent_checkbox_set(checkbox, value, handler):
    checkbox.stateChanged.disconnect(handler)
    checkbox.setChecked(value)
    checkbox.stateChanged.connect(handler)


class MapEditor(QtWidgets.QDialog):
    def __init__(self, mainWindow=None):
        super(MapEditor, self).__init__()
        self.main = mainWindow
        self.loaded_file = None

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
                btn = TileButton(self)
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
        button = self.buttonAtPosition(0, 0)
        self.setSelectedPosition(button)

    def moveSelection(self, y_move, x_move):
        if self.selectedPosition is None:
            return

        y, x = self.selectedPosition
        newpos = (y + y_move, x + x_move)

        if (newpos[0] < 0) or newpos[1] < 0:
            return

        button = self.buttonAtPosition(*newpos)
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
        self.saveButton = QtWidgets.QPushButton()
        self.loadButton = QtWidgets.QPushButton()
        self.loadFromSavedGameButton = QtWidgets.QPushButton()

        self.deleteButton.setText("Delete tile")
        self.doorButton.setText("Edit doors")
        self.saveButton.setText("Save to file")
        self.loadButton.setText("Load from file")
        self.loadFromSavedGameButton.setText("Load map from saved game")

        self.deleteButton.clicked.connect(self.deleteButtonClicked)
        self.doorButton.clicked.connect(self.doorButtonClicked)
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
        self.deleteButton.setEnabled(False)

        tileButtonLayout = QtWidgets.QHBoxLayout()
        tileButtonLayout.addWidget(self.deleteButton)
        tileButtonLayout.addWidget(self.doorButton)
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
                QtWidgets.qApp.quit()

    def clearGrid(self):
        for pos in _tiles:
            button = self.buttonAtPosition(*pos)
            button.setText("")
            button.clearDoors()
            button.setStyle(selected=False, start=False)

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

        attrs[player.OBJECT_VERSION_KEY] = obj_version
        attrs[player.TILES_KEY] = tile.crawler(start_tile)
        attrs[player.START_TILE_KEY] = start_tile.tile_id
        attrs['positions'] = {_tiles[pos].tile_id: list(pos) for pos in _tiles}

        return attrs

    def drawTileMap(self, start_tile, positions):
        for tile_id in positions:
            pos = tuple(positions[tile_id])
            tileobj = tile.get_tile_by_id(tile_id)
            if tileobj is None:
                continue

            _tiles[pos] = tileobj
            button = self.buttonAtPosition(*pos)
            button.setText(tileobj.tile_id)

            is_start = tileobj is start_tile
            button.setStyle(selected=False, start=is_start)
            button.redrawDoors()

    def deserialize(self, attrs):
        start_tile = tile.builder(attrs[player.TILES_KEY],
                                  attrs[player.START_TILE_KEY],
                                  attrs[player.OBJECT_VERSION_KEY])

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
            for loc in tiledata[tile.ITEMS_KEY]:
                tiledata[tile.ITEMS_KEY][loc] = []

            for loc in tiledata[tile.PEOPLE_KEY]:
                tiledata[tile.PEOPLE_KEY][loc] = []

            del tiledata[tile.ENTER_EVENT_KEY]
            del tiledata[tile.EXIT_EVENT_KEY]

        # build tilemap from list of tile data
        start_tile_name = attrs[player.START_TILE_KEY]
        start_tile = tile.builder(tilelist, start_tile_name, obj_version)

        # find lowest index tile in tilemap
        positions = getTilePositions(start_tile)
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

    def buttonAtPosition(self, y, x):
        return self.gridLayout.itemAtPosition(y, x).widget()

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
                old_start = self.buttonAtPosition(*self.startTilePosition)
                old_start.setStyle(selected=False, start=False)

            new_start = self.buttonAtPosition(*self.selectedPosition)
            new_start.setStyle(selected=True, start=True)
            self.startTilePosition = self.selectedPosition
            self.startTileCheckBox.setEnabled(False)

    def tileIDExists(self, tile_id):
        val = tile.get_tile_by_id(tile_id)
        return val is not None

    def loadFromSavedGameButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getOpenFileName(self, "Select saved game file to load",
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
        button = self.buttonAtPosition(*self.selectedPosition)

        reply = self.yesNoDialog("Are you sure?", "Are you sure you want to "
                                "delete this tile (tile ID is '%s')" % (tileobj.tile_id))
        if not reply:
            return

        self.disconnectSurroundingTiles(tileobj, self.selectedPosition)
        del _tiles[self.selectedPosition]
        button.setText("")

        if self.startTilePosition == self.selectedPosition:
            self.startTilePosition = None

        button.setStyle(selected=False, start=False)
        button.redrawDoors()

    def doorButtonClicked(self):
        tileobj = _tiles[self.selectedPosition]
        button = self.buttonAtPosition(*self.selectedPosition)

        doors_dialog = DoorEditor(self, tileobj)
        doors_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        doors_dialog.exec_()

    def saveButtonClicked(self):
        if self.loaded_file is None:
            self.saveAsButtonClicked()
        else:
            self.saveToFile(self.loaded_file)

    def saveAsButtonClicked(self):
        if self.startTilePosition is None:
            self.errorDialog("Unable to save map", "No start tile is set. You "
                             "must set a start tile before saving.")
            return

        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getSaveFileName(self, "Select save file",
                             "", "All Files (*);;Text Files (*.txt)",
                                                 options=options)

        self.saveToFile(filename)

    def saveToFile(self, filename):
        with open(filename, 'w') as fh:
            json.dump(self.serialize(), fh)

    def loadButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getOpenFileName(self, "Select file to open",
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

        self.loaded_file = filename

    def getButtonPosition(self, button):
        idx = self.gridLayout.indexOf(button)
        return self.gridLayout.getItemPosition(idx)[:2]

    def tileAtPosition(self, y, x):
        pos = (y, x)
        if pos not in _tiles:
            return None

        return _tiles[pos]

    def surroundingTilePositions(self, position):
        def _fetch_tile(pos, yoff, xoff):
            oldy, oldx = pos
            newy = oldy + yoff
            newx = oldx + xoff

            if newy < 0: return None
            if newx < 0: return None

            newpos = (newy, newx)
            if newpos not in _tiles:
                return None

            return newpos

        north = _fetch_tile(position, -1, 0)
        south = _fetch_tile(position, 1, 0)
        east = _fetch_tile(position, 0, 1)
        west = _fetch_tile(position, 0, -1)

        return north, south, east, west

    def setSelectedPosition(self, button):
        if self.selectedPosition is not None:
            oldstart = self.selectedPosition == self.startTilePosition
            oldbutton = self.buttonAtPosition(*self.selectedPosition)
            oldbutton.setStyle(selected=False, start=oldstart)

        self.selectedPosition = self.getButtonPosition(button)

        newstart = self.selectedPosition == self.startTilePosition
        newfilled = self.selectedPosition in _tiles
        button.setStyle(selected=True, start=newstart)

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

        for obj in [self.doorButton, self.deleteButton]:
            if obj.isEnabled() != filled:
                obj.setEnabled(filled)

        button.setFocus(True)

    def onMiddleClick(self, button):
        pass

    def onRightClick(self, button):
        self.setSelectedPosition(button)

    def runTileBuilderDialog(self, position):
        settings = forms.TileSettings()

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
            dialog.setWindowIcon(QtGui.QIcon(self.main.iconPath))
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
        north, south, east, west = self.surroundingTilePositions(position)
        adjacent_tiles = {'north': north, 'south': south, 'east': east, 'west': west}

        for direction in adjacent_tiles:
            adjacent_tilepos = adjacent_tiles[direction]

            if not adjacent_tilepos:
                continue

            adjacent_tileobj = self.tileAtPosition(*adjacent_tilepos)
            setattr(tileobj, direction, None)

            # re-draw the tile we just disconnected from
            button = self.buttonAtPosition(*adjacent_tilepos)
            button.update()

            reverse_direction = tile.reverse_direction(direction)
            reverse_pointer = getattr(adjacent_tileobj, reverse_direction)

            if reverse_pointer and reverse_pointer.is_door():
                reverse_pointer.replacement_tile = None
            else:
                setattr(adjacent_tileobj, tile.reverse_direction(direction), None)

    def connectSurroundingTiles(self, tileobj, position):
        north, south, east, west = self.surroundingTilePositions(position)
        adjacent_tiles = {'north': north, 'south': south, 'east': east, 'west': west}

        for direction in adjacent_tiles:
            adjacent_tilepos = adjacent_tiles[direction]

            if not adjacent_tilepos:
                continue

            adjacent_tileobj = self.tileAtPosition(*adjacent_tilepos)
            setattr(tileobj, direction, adjacent_tileobj)

            # re-draw the tile we just connected to
            button = self.buttonAtPosition(*adjacent_tilepos)
            button.update()

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
            button.setStyle(selected=True, start=False)
            self.connectSurroundingTiles(tileobj, position)

        button.setText(str(tileobj.tile_id))
        self.setSelectedPosition(button)

