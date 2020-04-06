import os
import json
import zlib
import copy
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_map_maker.utils import yesNoDialog, errorDialog
from text_game_map_maker import forms, scrollarea, tgmdata
from text_game_map_maker.door_editor import DoorEditor
from text_game_map_maker.object_browsers import TileItemBrowser, SavedItemBrowser
from text_game_map_maker import tile_button
from text_game_map_maker.qt_auto_form import QtAutoForm
from text_game_maker.game_objects import __object_model_version__ as obj_version

from text_game_maker.game_objects.person import Person, Context
from text_game_maker.game_objects.items import (Item, Food, Weapon, Bag,
    SmallBag, SmallTin, Coins, Blueprint, Paper, PaperBag, LargeContainer,
    Furniture, BoxOfMatches, Flashlight, Battery, Lockpick, StrongLockpick,
    Lighter, Machete
)

from text_game_maker.tile import tile
from text_game_maker.player import player


NUM_BUTTON_ROWS = 50
NUM_BUTTON_COLUMNS = 50

DEFAULT_WINDOW_WIDTH = 500
DEFAULT_WINDOW_HEIGHT = 400

NUM_BUTTONS_PER_SCREEN_HEIGHT = 6.0

BUTTON_ZOOM_INCREMENT = 14
FONT_ZOOM_INCREMENT = 1.0

DEFAULT_BUTTON_SIZE = 180
DEFAULT_FONT_SIZE = 14.0

MIN_BUTTON_SIZE = 45
MIN_FONT_SIZE = 1

MAX_BUTTON_SIZE = 400
MAX_FONT_SIZE = 25

SCROLL_UNITS_PER_CLICK = 120

MAP_BUILDER_SAVE_FILE_SUFFIX = "tgmdata"

_tiles = {}

_move_map = {
    'north': (-1, 0),
    'south': (1, 0),
    'east': (0, 1),
    'west': (0, -1)
}


class ZoomLevel(object):
    button_size = DEFAULT_BUTTON_SIZE
    font_size = DEFAULT_FONT_SIZE

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
    def __init__(self, primaryScreen, mainWindow):
        super(MapEditor, self).__init__()

        self.main = mainWindow
        self.primary_screen = primaryScreen
        self.loaded_file = None
        self.save_enabled = True
        self.copying = False
        self.last_selection_added = None
        self.tracking_tile_button_enter = False
        self.group_mask = []

        screensize = self.primary_screen.size()
        self.screen_width = screensize.width()
        self.screen_height = screensize.height()

        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.gridAreaLayout = QtWidgets.QHBoxLayout()
        self.buttonAreaLayout = QtWidgets.QHBoxLayout()
        self.buildToolbar()

        # Build scrollable grid area
        self.scrollArea = scrollarea.ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scroll_offset = 0

        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridAreaLayout.addWidget(self.scrollArea)

        self.font = QtGui.QFont()
        self.font.setPointSize(ZoomLevel.font_size)
        self.font.setFamily("Arial")

        self.mainLayout.addLayout(self.buttonAreaLayout)
        self.mainLayout.addLayout(self.gridAreaLayout)
        self.selectedPositions = []
        self.selectedPosition = None
        self.startTilePosition = None

        self.rows = NUM_BUTTON_ROWS
        self.columns = NUM_BUTTON_COLUMNS

        tile_button.TileButton.set_dimensions(ZoomLevel.button_size,
                                              ZoomLevel.button_size)
        for i in range(self.rows):
            for j in range(self.columns):
                btn = tile_button.TileButton(self)

                btn.setFont(self.font)
                btn.setAttribute(QtCore.Qt.WA_StyledBackground)
                btn.setFixedSize(ZoomLevel.button_size, ZoomLevel.button_size)
                btn.installEventFilter(btn)
                self.gridLayout.addWidget(btn, i, j)

        # Enable mouse tracking on scrollarea and all children
        self.scrollArea.setMouseTracking(True)

        # Set up shortcuts for arrow keys
        QtWidgets.QShortcut(QtGui.QKeySequence("right"), self, self.rightKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("left"), self, self.leftKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("up"), self, self.upKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("down"), self, self.downKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+right"), self, self.shiftRightKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+left"), self, self.shiftLeftKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+up"), self, self.shiftUpKeyPress)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+down"), self, self.shiftDownKeyPress)

    def moveSelection(self, y_move, x_move):
        if self.selectedPosition is None:
            return

        y, x = self.selectedPosition
        newpos = (y + y_move, x + x_move)

        if ((newpos[0] < 0) or (newpos[0] >= self.columns) or
            (newpos[1] < 0) or (newpos[1] >= self.rows)):
            return

        button = self.buttonAtPosition(*newpos)
        self.setSelectedPosition(button)

    def clearSelectedPositions(self):
        if self.selectedPositions:
            for pos in self.selectedPositions:
                b = self.buttonAtPosition(*pos)
                is_start = pos == self.startTilePosition
                b.setStyle(selected=False, start=is_start)

            self.selectedPositions = []

    def shiftArrowKeyPress(self, direction):
        if self.tracking_tile_button_enter:
            return

        if not self.last_selection_added:
            return

        y, x = self.last_selection_added
        yd, xd = _move_map[direction]
        newy, newx = y + yd, x + xd

        if (0 <= newy < NUM_BUTTON_ROWS) and (0 <= newx < NUM_BUTTON_COLUMNS):
            button = self.buttonAtPosition(newy, newx)
            self.addSelectedPosition(button)
            self.scrollArea.ensureWidgetVisible(button)

    def arrowKeyPress(self, direction):
        if self.selectedPositions:
            self.selectedPosition = self.selectedPositions[-1]

        if self.tracking_tile_button_enter:
            yd, xd = _move_map[direction]
            y, x = self.group_mask[-1]
            new_pos = (y + yd, x + xd)

            if (0 <= new_pos[0] < NUM_BUTTON_ROWS) and (0 <= new_pos[1] < NUM_BUTTON_COLUMNS):
                self.drawSelectionMask(new_pos)
                button = self.buttonAtPosition(*new_pos)
                self.scrollArea.ensureWidgetVisible(button)

        else:
            self.clearSelectedPositions()
            self.moveSelection(*_move_map[direction])

    def shiftLeftKeyPress(self):
        self.shiftArrowKeyPress('west')

    def shiftRightKeyPress(self):
        self.shiftArrowKeyPress('east')

    def shiftUpKeyPress(self):
        self.shiftArrowKeyPress('north')

    def shiftDownKeyPress(self):
        self.shiftArrowKeyPress('south')

    def leftKeyPress(self):
        self.arrowKeyPress('west')

    def rightKeyPress(self):
        self.arrowKeyPress('east')

    def upKeyPress(self):
        self.arrowKeyPress('north')

    def downKeyPress(self):
        self.arrowKeyPress('south')

    def buildToolbar(self):
        self.deleteButton = QtWidgets.QPushButton()
        self.clearButton = QtWidgets.QPushButton()
        self.doorButton = QtWidgets.QPushButton()
        self.wallButton = QtWidgets.QPushButton()
        self.itemButton = QtWidgets.QPushButton()
        self.moveButton = QtWidgets.QPushButton()
        self.copyButton = QtWidgets.QPushButton()
        self.saveButton = QtWidgets.QPushButton()
        self.loadButton = QtWidgets.QPushButton()
        self.savedObjectsButton = QtWidgets.QPushButton()
        self.loadFromSavedGameButton = QtWidgets.QPushButton()

        self.deleteButton.setText("Delete")
        self.clearButton.setText("Clear all")
        self.doorButton.setText("Doors..")
        self.wallButton.setText("Walls..")
        self.itemButton.setText("Items..")
        self.savedObjectsButton.setText("Saved objects..")
        self.moveButton.setText("Move")
        self.copyButton.setText("Copy")
        self.saveButton.setText("Save")
        self.loadButton.setText("Load")
        self.loadFromSavedGameButton.setText("Load from game save")

        self.deleteButton.clicked.connect(self.deleteButtonClicked)
        self.clearButton.clicked.connect(self.clearButtonClicked)
        self.doorButton.clicked.connect(self.doorButtonClicked)
        self.wallButton.clicked.connect(self.wallButtonClicked)
        self.itemButton.clicked.connect(self.itemButtonClicked)
        self.moveButton.clicked.connect(self.moveButtonClicked)
        self.copyButton.clicked.connect(self.copyButtonClicked)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.loadButton.clicked.connect(self.loadButtonClicked)
        self.savedObjectsButton.clicked.connect(self.savedObjectsButtonClicked)
        self.loadFromSavedGameButton.clicked.connect(self.loadFromSavedGameButtonClicked)

        self.startTileCheckBox = QtWidgets.QCheckBox()
        self.startTileCheckBox.setStyleSheet("margin-left:50%; margin-right:50%;")
        self.startTileCheckBox.setChecked(False)
        self.startTileCheckBox.setEnabled(False)
        self.startTileCheckBox.stateChanged.connect(self.setStartTile)

        label = QtWidgets.QLabel("Start tile")
        label.setAlignment(QtCore.Qt.AlignCenter)
        checkBoxLayout = QtWidgets.QVBoxLayout()
        checkBoxLayout.addWidget(label)
        checkBoxLayout.addWidget(self.startTileCheckBox)
        checkBoxLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.doorButton.setEnabled(False)
        self.wallButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.itemButton.setEnabled(False)

        tileButtonLayout = QtWidgets.QHBoxLayout()
        tileButtonLayout.addWidget(self.doorButton)
        tileButtonLayout.addWidget(self.wallButton)
        tileButtonLayout.addWidget(self.itemButton)
        tileButtonLayout.addWidget(self.savedObjectsButton)
        tileButtonLayout.addLayout(checkBoxLayout)
        tileButtonGroup = QtWidgets.QGroupBox("Tile Contents")
        tileButtonGroup.setAlignment(QtCore.Qt.AlignCenter)
        tileButtonGroup.setLayout(tileButtonLayout)

        moveButtonLayout = QtWidgets.QHBoxLayout()
        moveButtonLayout.addWidget(self.moveButton)
        moveButtonLayout.addWidget(self.copyButton)
        moveButtonLayout.addWidget(self.deleteButton)
        moveButtonLayout.addWidget(self.clearButton)
        moveButtonGroup = QtWidgets.QGroupBox("Tiles")
        moveButtonGroup.setAlignment(QtCore.Qt.AlignCenter)
        moveButtonGroup.setLayout(moveButtonLayout)

        fileButtonLayout = QtWidgets.QHBoxLayout()
        fileButtonLayout.addWidget(self.saveButton)
        fileButtonLayout.addWidget(self.loadButton)
        fileButtonLayout.addWidget(self.loadFromSavedGameButton)
        fileButtonGroup = QtWidgets.QGroupBox("File")
        fileButtonGroup.setAlignment(QtCore.Qt.AlignCenter)
        fileButtonGroup.setLayout(fileButtonLayout)

        compass = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(self.main.compassPath,"1")
        pixmap = pixmap.scaled(128, 128)
        compass.setPixmap(pixmap)
        compassLayout = QtWidgets.QHBoxLayout()
        compassLayout.addWidget(compass)
        compassGroup = QtWidgets.QGroupBox()
        compassGroup.setLayout(compassLayout)
        compassGroup.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.buttonAreaLayout.addWidget(compassGroup)
        self.buttonAreaLayout.addWidget(tileButtonGroup)
        self.buttonAreaLayout.addWidget(moveButtonGroup)
        self.buttonAreaLayout.addWidget(fileButtonGroup)

    def warningBeforeQuit(self):
        return yesNoDialog(self, "Are you sure?", "Are you sure you want to quit?"
                                 " You will lose any unsaved data.")

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            # If we're in the middle of a move/copy operation, escape key should cancel it
            if self.tracking_tile_button_enter:
                self.eraseSelectionMask()
                self.tracking_tile_button_enter = False
                self.group_mask = []

            # Otherwise, escape key should close the main window (after a warning)
            else:
                if self.warningBeforeQuit():
                    QtWidgets.qApp.quit()

    def setSaveEnabled(self, value):
        if value == self.save_enabled:
            return

        self.saveButton.setEnabled(value)
        self.main.saveAction.setEnabled(value)
        self.save_enabled = value

    def wheelEvent(self, event):
        num_clicks = event.angleDelta().y() / SCROLL_UNITS_PER_CLICK

        if num_clicks > 0:
            self.increaseZoomLevel(False, num_clicks)
        else:
            self.decreaseZoomLevel(False, abs(num_clicks))

    def resizeGridView(self, button_size, font_size):
        tile_button.TileButton.set_dimensions(button_size, button_size)

        for y in range(self.rows):
            for x in range(self.columns):
                btn = self.buttonAtPosition(y, x)

                self.font.setPointSize(font_size)
                btn.setFont(self.font)
                btn.setFixedSize(button_size, button_size)

                if (y, x) in _tiles:
                    btn.redrawDoors()

    def setDefaultZoomLevel(self):
        ZoomLevel.button_size = DEFAULT_BUTTON_SIZE
        ZoomLevel.font_size = DEFAULT_FONT_SIZE
        self.resizeGridView(ZoomLevel.button_size, ZoomLevel.font_size)

    def increaseZoomLevel(self, _, num=1):
        moved = 0
        while ((num > 0) and (ZoomLevel.button_size < MAX_BUTTON_SIZE) and
               (ZoomLevel.font_size < MAX_FONT_SIZE)):
            ZoomLevel.button_size += BUTTON_ZOOM_INCREMENT
            ZoomLevel.font_size += FONT_ZOOM_INCREMENT
            moved += 1
            num -= 1

        if moved == 0:
            return

        self.resizeGridView(ZoomLevel.button_size, ZoomLevel.font_size)

    def decreaseZoomLevel(self, _, num=1):
        moved = 0
        while((num > 0) and (ZoomLevel.button_size > MIN_BUTTON_SIZE) and
              (ZoomLevel.font_size > MIN_FONT_SIZE)):
            ZoomLevel.button_size -= BUTTON_ZOOM_INCREMENT
            ZoomLevel.font_size -= FONT_ZOOM_INCREMENT
            moved += 1
            num -= 1

        if moved == 0:
            return

        self.resizeGridView(ZoomLevel.button_size, ZoomLevel.font_size)

    def clearAllTiles(self):
        for pos in list(_tiles.keys()):
            button = self.buttonAtPosition(*pos)
            button.setText("")
            button.clearDoors()
            del _tiles[pos]
            button.setStyle(selected=False, start=False)

        for pos in self.selectedPositions + [self.selectedPosition]:
            if not pos:
                continue

            button = self.buttonAtPosition(*pos)
            button.setStyle()

        self.startTilePosition = None
        self.selectedPosition = None
        self.selectedPositions = []

        self.enableSelectionDependentItems()

    def tile_id_in_map_data(self, tile_list, tile_id):
        for tiledata in tile_list:
            if tiledata["tile_id"] == tile_id:
                return True

        return False

    def serialize(self):
        return tgmdata.serialize(_tiles[self.startTilePosition], _tiles)

    def drawTileMap(self, start_tile, positions):
        for tile_id in positions:
            pos = tuple(positions[tile_id])
            tileobj = tile.get_tile_by_id(tile_id)
            if tileobj is None:
                continue

            _tiles[pos] = tileobj
            button = self.buttonAtPosition(*pos)
            button.setText(tileobj.map_identifier)

            is_start = tileobj is start_tile
            button.setStyle(selected=False, start=is_start)
            button.redrawDoors()

    def deserialize(self, attrs):
        start_tile = tgmdata.deserialize(attrs)
        self.clearAllTiles()
        self.drawTileMap(start_tile, attrs['positions'])
        self.startTilePosition = tuple(attrs['positions'][start_tile.tile_id])

    def deserializeFromSaveFile(self, attrs):
        if (player.TILES_KEY not in attrs) or (player.START_TILE_KEY not in attrs):
            return False

        # Remove items, people and events, we're not dealing with them here
        tilelist = attrs[player.TILES_KEY]
        for tiledata in tilelist:
            #del tiledata[tile.ITEMS_KEY]
            del tiledata[tile.PEOPLE_KEY]
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

        self.clearAllTiles()
        self.drawTileMap(start_tile, positions)
        self.startTilePosition = positions[start_tile.tile_id]

        return True

    def buttonAtPosition(self, y, x):
        item = self.gridLayout.itemAtPosition(y, x)
        if item is None:
            return None

        return item.widget()

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

    def setStartTile(self, state=None):
        if self.selectedPosition == self.startTilePosition:
            return

        if self.selectedPosition not in _tiles:
            return

        if self.startTilePosition is not None:
            # Set current start tile colour back to default
            old_start = self.buttonAtPosition(*self.startTilePosition)
            old_start.setStyle(selected=False, start=False)

        if not self.startTileCheckBox.isChecked():
            self.startTileCheckBox.stateChanged.disconnect(self.setStartTile)
            self.startTileCheckBox.setChecked(True)
            self.startTileCheckBox.stateChanged.connect(self.setStartTile)

        new_start = self.buttonAtPosition(*self.selectedPosition)
        new_start.setStyle(selected=True, start=True)
        self.startTilePosition = self.selectedPosition
        self.startTileCheckBox.setEnabled(False)
        self.main.startTileAction.setEnabled(False)
        self.setSaveEnabled(True)

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
            errorDialog(self, "Can't find file", "There doesn't seem to be a "
                        "file called '%s'" % filename)

        try:
            with open(filename, 'rb') as fh:
                data = fh.read()
                strdata = zlib.decompress(data).decode("utf-8")
                attrs = json.loads(strdata)
        except Exception as e:
            errorDialog(self, "Error loading saved game state",
                        "Unable to load saved game data from file %s: %s"
                             % (filename, str(e)))
            return

        self.deserializeFromSaveFile(attrs)

        if _tiles:
            self.clearButton.setEnabled(True)

    def deleteButtonClicked(self):
        tiles = self.getSelectedPositions()

        if not tiles:
            errorDialog(self, "Unable to delete tile", "No selected tiles")
            return

        if len(tiles) == 1:
            tileobj = _tiles[self.selectedPosition]
            msg = ("Are you sure you want to delete this tile (tile ID is '%s')"
                   % tileobj.tile_id)
        else:
            msg = "Are you sure you want to delete %d tiles?" % len(tiles)

        reply = yesNoDialog(self, "Are you sure?", msg)
        if not reply:
            return

        for pos in tiles:
            self.deleteTile(pos)

        self.setSelectedPosition(self.buttonAtPosition(*tiles[-1]))

    def deleteTile(self, pos):
        button = self.buttonAtPosition(*pos)
        tileobj = self.tileAtPosition(*pos)

        tile.unregister_tile_id(tileobj.tile_id)
        self.disconnectSurroundingTiles(tileobj, *pos)
        del _tiles[pos]
        button.setText("")

        if self.startTilePosition == pos:
            self.startTilePosition = None

        button.setStyle(selected=False, start=False)
        button.redrawDoors()

        # Did we delete the last tile?
        if _tiles:
            # If not, enable saving to file (if it was disabled)
            self.setSaveEnabled(True)
        else:
            # If yes, disable button for clearing all tiles
            self.clearButton.setEnabled(False)

    def getSelectedPositions(self):
        positions = [p for p in self.selectedPositions if p in _tiles]
        if self.selectedPosition in _tiles and self.selectedPosition not in positions:
            positions.append(self.selectedPosition)

        return positions

    def onTileButtonEnter(self, button):
        self.drawSelectionMask(self.getButtonPosition(button))

    def eraseSelectionMask(self):
        for pos in self.group_mask:
            b = self.buttonAtPosition(*pos)
            if not b:
                continue

            is_selected = (pos == self.selectedPosition) or (pos in self.selectedPositions)
            is_start = pos == self.startTilePosition
            b.setStyle(selected=is_selected, start=is_start)

    def drawSelectionMask(self, new_pos):
        old_pos = self.group_mask[-1]

        delta_y = new_pos[0] - old_pos[0]
        delta_x = new_pos[1] - old_pos[1]

        # Calculate positions for new selection mask
        new_mask = []
        for pos in self.group_mask:
            new_mask.append((pos[0] + delta_y, pos[1] + delta_x))

        # Re-draw old selection mask to put tiles back to normal
        self.eraseSelectionMask()

        # Draw selection mask at new position
        for pos in new_mask:
            b = self.buttonAtPosition(*pos)
            if not b:
                continue

            b.setStyle(selection_mask=True)

        self.group_mask = new_mask

    def clearButtonClicked(self):
        reply = yesNoDialog(self, "Really clear all tiles?", "Are you sure you "
                            "want to clear all tiles? you will lose any unsaved data.")

        if not reply:
            return

        self.clearAllTiles()
        self.clearButton.setEnabled(False)

    def moveButtonClicked(self):
        # Are we already in the middle of a copy/move operation?
        if self.tracking_tile_button_enter:
            return

        self.copying = False
        # Enable tracking of tile button enter events
        self.tracking_tile_button_enter = True

        # Get positions of all the tiles we need to move
        self.group_mask = self.getSelectedPositions()

        # If cursor is currently over a tile, initialize selection mask there
        if tile_button.TileButton.hovering:
            pos = self.getButtonPosition(tile_button.TileButton.hovering)
            self.drawSelectionMask(pos)

    def copyButtonClicked(self):
        # Are we already in the middle of a copy/move operation?
        if self.tracking_tile_button_enter:
            return

        self.copying = True
        # Enable tracking of tile button enter events
        self.tracking_tile_button_enter = True

        # Get positions of all the tiles we need to copy
        self.group_mask = self.getSelectedPositions()

        # If cursor is currently over a tile, initialize selection mask there
        if tile_button.TileButton.hovering:
            pos = self.getButtonPosition(tile_button.TileButton.hovering)
            self.drawSelectionMask(pos)

    def doorButtonClicked(self):
        tileobj = _tiles[self.selectedPosition]
        button = self.buttonAtPosition(*self.selectedPosition)

        doors_dialog = DoorEditor(self, tileobj)
        doors_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        doors_dialog.exec_()
        self.setSaveEnabled(True)

    def itemButtonClicked(self):
        tileobj = _tiles[self.selectedPosition]
        items_dialog = TileItemBrowser(self, tileobj)
        items_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        items_dialog.exec_()
        self.setSaveEnabled(True)

    def savedObjectsButtonClicked(self):
        items_dialog = SavedItemBrowser(self, None)
        items_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        items_dialog.exec_()
        self.setSaveEnabled(True)

    def wallButtonClicked(self):
        tileobj = _tiles[self.selectedPosition]
        button = self.buttonAtPosition(*self.selectedPosition)

        settings = forms.WallSettings()

        # Populate form with existing wall configuration for selected tile
        for direction in ['north', 'south', 'east', 'west']:
            adj = getattr(tileobj, direction)
            val = True if (adj is None) or adj.is_door() else False
            setattr(settings, direction, val)

        # Display form
        dialog = QtAutoForm(settings, title="Edit walls",
                            formTitle="Select directions to be blocked by walls",
                            spec=settings.spec)

        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.setWindowIcon(QtGui.QIcon(self.main.iconPath))
        dialog.exec_()

        if not dialog.wasAccepted():
            # Dialog was cancelled or closed
            return None

        # Apply form settings to selected tile
        for direction in ['north', 'south', 'east', 'west']:
            adj = getattr(tileobj, direction)
            had_wall = True if (adj is None) or adj.is_door() else False
            has_wall = getattr(settings, direction)

            # No change, we're done with this iteration
            if had_wall == has_wall:
                continue

            if has_wall:
                # Adding a wall
                setattr(adj, tile.reverse_direction(direction), None)
                setattr(tileobj, direction, None)
            else:
                # Removing a wall
                oldy, oldx = self.selectedPosition
                deltay, deltax = _move_map[direction]
                newy, newx = oldy + deltay, oldx + deltax

                # Adjacent tile is off the grid, we're done with this iteration
                if ((newy < 0) or (newy >= self.rows) or
                    (newx < 0) or (newx >= self.columns)):
                    continue

                adj_tile = self.tileAtPosition(newy, newx)
                if adj_tile is None:
                    # No tile here, we're done with this iteration
                    continue

                setattr(adj_tile, tile.reverse_direction(direction), tileobj)
                setattr(tileobj, direction, adj_tile)

        button.update()
        self.redrawSurroundingTiles(*self.selectedPosition)
        self.setSaveEnabled(True)

    def saveFileDialog(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setDefaultSuffix(MAP_BUILDER_SAVE_FILE_SUFFIX)
        dialog.setNameFilter("Text Game Map Data Files (*.%s)"
                             % MAP_BUILDER_SAVE_FILE_SUFFIX)

        if dialog.exec_():
            filenames = dialog.selectedFiles()
            if len(filenames) != 1:
                return None

            return filenames[0]

        return None

    def saveButtonClicked(self):
        if self.loaded_file is None:
            self.saveAsButtonClicked()
        else:
            self.saveToFile(self.loaded_file)

    def saveAsButtonClicked(self):
        if self.startTilePosition is None:
            errorDialog(self, "Unable to save map", "No start tile is set. You "
                        "must set a start tile before saving.")
            return

        filename = self.saveFileDialog()
        # Cancelled, or empty string?
        if (filename == None) or (filename.strip() == ""):
            return

        self.saveToFile(filename)

    def saveToFile(self, filename):
        try:
            string_data = json.dumps(self.serialize())
            compressed = zlib.compress(bytes(string_data, encoding="utf8"))

            with open(filename, 'wb') as fh:
                fh.write(compressed)
        except Exception:
            errorDialog(self, "Error saving map data",
                        "Unable to save map data to file %s:\n\n%s"
                        % (filename, traceback.format_exc()))

        self.setSaveEnabled(False)

    def loadFromFile(self, filename):
        if not os.path.exists(filename):
            errorDialog(self, "Can't find file", "There doesn't seem to be a "
                        "file called '%s'" % filename)
            return

        try:
            with open(filename, 'rb') as fh:
                strdata = fh.read()

            decompressed = zlib.decompress(strdata).decode("utf-8")
            attrs = json.loads(decompressed)
            self.deserialize(attrs)
        except Exception:
            errorDialog(self, "Error loading saved map data",
                        "Unable to load saved map data from file %s:\n\n%s"
                        % (filename, traceback.format_exc()))

        self.loaded_file = filename
        if _tiles:
            self.clearButton.setEnabled(True)

        self.setSaveEnabled(False)

    def loadButtonClicked(self):
        filedialog = QtWidgets.QFileDialog
        options = filedialog.Options()
        options |= filedialog.DontUseNativeDialog
        filename, _ = filedialog.getOpenFileName(self, "Select file to open",
                             "", "All Files (*);;Text Files (*.txt)",
                                                 options=options)

        if filename.strip() == '':
            return

        self.loadFromFile(filename)

    def getButtonPosition(self, button):
        idx = self.gridLayout.indexOf(button)
        return self.gridLayout.getItemPosition(idx)[:2]

    def tileAtPosition(self, y, x):
        pos = (y, x)
        if pos not in _tiles:
            return None

        return _tiles[pos]

    def surroundingTilePositions(self, y, x):
        def _fetch_tile(y, x, yoff, xoff):
            oldy, oldx = y, x
            newy = oldy + yoff
            newx = oldx + xoff

            if newy < 0: return None
            if newx < 0: return None

            newpos = (newy, newx)
            if newpos not in _tiles:
                return None

            return newpos

        north = _fetch_tile(y, x, -1, 0)
        south = _fetch_tile(y, x, 1, 0)
        east = _fetch_tile(y, x, 0, 1)
        west = _fetch_tile(y, x, 0, -1)

        return north, south, east, west

    def enableSelectionDependentItems(self):
        exactly_one = self.selectedPosition in _tiles
        one_or_more = exactly_one

        if not exactly_one:
            for pos in self.selectedPositions:
                if pos in _tiles:
                    one_or_more = True
                    break

        # These items require one or more tiles to be selected
        for obj in [self.moveButton, self.copyButton, self.main.copyTileAction,
                    self.main.moveTileAction, self.deleteButton,
                    self.main.deleteTileAction]:
            if obj.isEnabled != one_or_more:
                obj.setEnabled(one_or_more)

        # These items require exactly one tile to be selected
        for obj in [self.doorButton, self.wallButton, self.itemButton,
                    self.main.editDoorsAction, self.main.editWallsAction,
                    self.main.editTileAction, self.main.editItemsAction]:
            if obj.isEnabled() != exactly_one:
                obj.setEnabled(exactly_one)

    def setSelectedPosition(self, button):
        # De-select group if any is selected
        self.clearSelectedPositions()

        if self.selectedPosition is not None:
            oldstart = self.selectedPosition == self.startTilePosition
            oldbutton = self.buttonAtPosition(*self.selectedPosition)
            oldbutton.setStyle(selected=False, start=oldstart)

        self.selectedPosition = self.getButtonPosition(button)
        newstart = self.selectedPosition == self.startTilePosition
        newfilled = self.selectedPosition in _tiles
        button.setStyle(selected=True, start=newstart)

        filled = self.selectedPosition in _tiles

        if self.selectedPosition == self.startTilePosition:
            _silent_checkbox_set(self.startTileCheckBox, True, self.setStartTile)
            self.startTileCheckBox.setEnabled(False)
            self.main.startTileAction.setEnabled(False)
        elif filled:
            self.startTileCheckBox.setEnabled(True)
            _silent_checkbox_set(self.startTileCheckBox, False, self.setStartTile)
            self.main.startTileAction.setEnabled(True)
        else:
            _silent_checkbox_set(self.startTileCheckBox, False, self.setStartTile)
            self.startTileCheckBox.setEnabled(False)
            self.main.startTileAction.setEnabled(False)

        button.setFocus(True)
        self.last_selection_added = self.selectedPosition
        self.scrollArea.ensureWidgetVisible(button)
        self.enableSelectionDependentItems()

    def addSelectedPosition(self, button):
        if self.selectedPosition is not None:
            self.selectedPositions.append(self.selectedPosition)
            self.selectedPosition = None

        pos = self.getButtonPosition(button)
        self.last_selection_added = pos
        if pos in self.selectedPositions:
            return

        self.selectedPositions.append(pos)
        is_start = pos == self.startTilePosition
        button.setStyle(selected=True, start=is_start)
        self.enableSelectionDependentItems()

        # Start tile checkbox should always be disabled with multiple tiles selected
        _silent_checkbox_set(self.startTileCheckBox, False, self.setStartTile)
        self.startTileCheckBox.setEnabled(False)
        self.main.startTileAction.setEnabled(False)

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
            settings.name_from_north = tileobj.name_from_dir["north"]
            settings.name_from_south = tileobj.name_from_dir["south"]
            settings.name_from_east = tileobj.name_from_dir["east"]
            settings.name_from_west = tileobj.name_from_dir["west"]
        else:
            tileobj = tile.Tile()
            settings.tile_id = "tile%d" % tile.Tile.tile_id
            settings.name = "a room"
            settings.description = "in a room"

        complete = False
        while not complete:
            dialog = QtAutoForm(settings, title="Tile attributes",
                                formTitle="Set attributes of currently selected tile",
                                scrollable=True, spec=settings.spec)

            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.setWindowIcon(QtGui.QIcon(self.main.iconPath))
            dialog.exec_()

            if not dialog.wasAccepted():
                return None

            if str(settings.tile_id).strip() == '':
                errorDialog(self, "Invalid tile ID", "tile ID field cannot be empty")
            elif (tileobj.tile_id != settings.tile_id) and self.tileIDExists(settings.tile_id):
                errorDialog(self, "Unable to create tile", "Tile ID '%s' already in use!"
                                 % settings.tile_id)
            else:
                complete = True

        if settings.tile_id != tileobj.tile_id:
            tileobj.set_tile_id(settings.tile_id)

        tileobj.description = settings.description
        tileobj.name = settings.name
        tileobj.original_name = settings.name
        tileobj.first_visit_message = settings.first_visit_message
        tileobj.first_visit_message_in_dark = settings.first_visit_message_in_dark
        tileobj.dark = settings.dark
        tileobj.smell_description = settings.smell_description
        tileobj.ground_smell_description = settings.ground_smell_description
        tileobj.ground_taste_description = settings.ground_taste_description
        tileobj.name_from_dir["north"] = settings.name_from_north
        tileobj.name_from_dir["south"] = settings.name_from_south
        tileobj.name_from_dir["east"] = settings.name_from_east
        tileobj.name_from_dir["west"] = settings.name_from_west
        return tileobj

    def redrawSurroundingTiles(self, y, x):
        north, south, east, west = self.surroundingTilePositions(y, x)
        adjacent_tiles = {'north': north, 'south': south, 'east': east, 'west': west}

        for direction in adjacent_tiles:
            adjacent_tilepos = adjacent_tiles[direction]

            if not adjacent_tilepos:
                continue

            button = self.buttonAtPosition(*adjacent_tilepos)
            button.update()

    def disconnectSurroundingTiles(self, tileobj, y, x):
        north, south, east, west = self.surroundingTilePositions(y, x)
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

    def connectSurroundingTiles(self, tileobj, y, x):
        north, south, east, west = self.surroundingTilePositions(y, x)
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

    def editSelectedTile(self):
        if self.selectedPosition is None:
            return

        self.onLeftClick(self.buttonAtPosition(*self.selectedPosition))

    def moveSelectionMask(self):
        # Get positions of all the original tiles from the selection mask
        orig_positions = self.getSelectedPositions()

        src_tiles = {}

        # Populate & connect all the new tiles
        for i in range(len(orig_positions)):
            pos = orig_positions[i]
            src_tile = self.tileAtPosition(*pos)
            directions = ['north', 'south', 'east', 'west']

            # Handle new tile connections
            for attr in directions:
                delta_y, delta_x = _move_map[attr]
                adj_pos = (pos[0] + delta_y, pos[1] + delta_x)

                # If this tile is connected to a tile we're not moving, we'll
                # need to sever that connection
                if adj_pos not in orig_positions:
                    adj_tile = self.tileAtPosition(*adj_pos)
                    if adj_tile:
                        setattr(src_tile, attr, None)
                        setattr(adj_tile, tile.reverse_direction(attr), None)
                        adj_button = self.buttonAtPosition(*adj_pos)
                        is_start = adj_pos == self.selectedPosition
                        adj_button.setStyle(start=is_start)

                    continue

            # Save src tile for the next iteration so we can delete it now
            src_tiles[pos] = _tiles[pos]

            # Delete tile from old position
            del _tiles[pos]

            old_button = self.buttonAtPosition(*pos)
            old_button.setText("")
            old_button.setStyle()
            old_button.redrawDoors()

        # Loop over buttons again to draw new tiles; we need two seperate
        # loops for drawing the old tile positions and drawing the new
        # tile positions after moving, in case the two groups overlap
        for i in range(len(orig_positions)):
            pos = orig_positions[i]
            src_tile = src_tiles[pos]

            # Add tile to new position
            _tiles[self.group_mask[i]] = src_tile

            button = self.buttonAtPosition(*self.group_mask[i])
            button.setText(src_tile.map_identifier)

            # Handle the case where start tile was moved - need to change
            # start tile position
            if self.startTilePosition == pos:
                self.startTilePosition = self.group_mask[i]
                button.setStyle(selected=True, start=True)
            else:
                button.setStyle()

            button.redrawDoors()

    def getCopiedTileId(self, tile_id):
        base = tile_id + "_copy"
        if tile.get_tile_by_id(base) is None:
            return base

        num = 1
        while True:
            numbered_copy = base + str(num)
            if tile.get_tile_by_id(numbered_copy) is None:
                return numbered_copy

            num += 1

    def copySelectionMask(self):
        # Get positions of all the original tiles from the selection mask
        orig_positions = self.getSelectedPositions()

        # Map of source tile IDs to copied tile IDs
        tile_id_map = {}

        # Create all the new tiles
        new_tiles = []
        for i in range(len(orig_positions)):
            src_tile = self.tileAtPosition(*orig_positions[i])
            tileobj = src_tile.copy()
            tileobj.set_tile_id(self.getCopiedTileId(src_tile.tile_id))
            tile_id_map[src_tile.tile_id] = tileobj.tile_id
            new_tiles.append(tileobj)

        # Populate & connect all the new tiles
        for i in range(len(orig_positions)):
            src_tile = self.tileAtPosition(*orig_positions[i])
            dest_tile = new_tiles[i]
            directions = ['north', 'south', 'east', 'west']

            # Handle new tile connections
            for attr in directions:
                src_adj = getattr(src_tile, attr)
                if src_adj is None:
                    dest_adj = None

                elif src_adj.is_door():
                    door_copy = copy.deepcopy(src_adj)
                    door_copy.tile_id = None
                    door_copy.set_tile_id(self.getCopiedTileId(src_adj.tile_id))
                    door_copy.src_tile = dest_tile
                    door_copy.replacement_tile = None
                    dest_adj = door_copy

                elif src_adj.tile_id in tile_id_map:
                    copy_name = tile_id_map[src_adj.tile_id]
                    dest_adj = tile.get_tile_by_id(copy_name)
                    if dest_adj is None:
                        setattr(dest_tile, attr, None)
                        continue

                    reverse_ptr = getattr(dest_adj, tile.reverse_direction(attr))
                    if reverse_ptr and reverse_ptr.is_door():
                        reverse_ptr.replacement_tile = dest_tile
                else:
                    dest_adj = None

                setattr(dest_tile, attr, dest_adj)

            _tiles[self.group_mask[i]] = dest_tile
            button = self.buttonAtPosition(*self.group_mask[i])
            button.setText(dest_tile.map_identifier)
            button.setStyle()
            button.redrawDoors()

    def setSelectionMask(self):
        if self.copying:
            self.copySelectionMask()
        else:
            self.moveSelectionMask()

        self.setSaveEnabled(True)
        self.tracking_tile_button_enter = False
        self.group_mask = []

    def onMiddleClick(self, button):
        pass

    def onRightClick(self, button):
        if self.group_mask:
            self.setSelectionMask()
            return

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self.addSelectedPosition(button)
        else:
            self.setSelectedPosition(button)

    def onLeftClick(self, button):
        if self.group_mask:
            self.setSelectionMask()
            return

        is_first_tile = (not _tiles)
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
            self.connectSurroundingTiles(tileobj, *position)

        button.setText(tileobj.map_identifier)
        self.setSelectedPosition(button)

        if is_first_tile:
            self.clearButton.setEnabled(True)

        self.setSaveEnabled(True)
