from text_game_map_maker import forms
from text_game_map_maker.qt_auto_form import QtAutoForm
from text_game_map_maker.utils import yesNoDialog, errorDialog

from text_game_maker.tile import tile
from PyQt5 import QtWidgets, QtCore, QtGui


class DoorEditor(QtWidgets.QDialog):
    def __init__(self, parent, tileobj):
        super(DoorEditor, self).__init__(parent=parent)

        self.door_id = 1
        self.parent = parent
        self.tile = tileobj
        self.directions = {}

        for direction in ['north', 'south', 'east', 'west']:
            neighbour = getattr(tileobj, direction)
            if (neighbour is not None) and neighbour.is_door():
                self.directions[direction] = neighbour

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(['door ID', 'door type', 'direction'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        self.populateTable()
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        buttonBox = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.addButton = QtWidgets.QPushButton()
        self.editButton = QtWidgets.QPushButton()
        self.deleteButton = QtWidgets.QPushButton()
        self.addButton.setText("Add door")
        self.editButton.setText("Edit door")
        self.deleteButton.setText("Delete door")

        self.editButton.clicked.connect(self.editButtonClicked)
        self.addButton.clicked.connect(self.addButtonClicked)
        self.deleteButton.clicked.connect(self.deleteButtonClicked)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.editButton)
        buttonLayout.addWidget(self.deleteButton)
        self.buttonGroupBox = QtWidgets.QGroupBox("")
        self.buttonGroupBox.setLayout(buttonLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.buttonGroupBox)
        mainLayout.addWidget(self.table)
        mainLayout.addWidget(buttonBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Minimum)
        self.setSizePolicy(sizePolicy)

        self.setLayout(mainLayout)
        self.setWindowTitle("Door Editor")

    def populateTable(self):
        self.table.setRowCount(0)
        for direction in self.directions:
            self.addRow(self.directions[direction], direction)

    def sizeHint(self):
        return QtCore.QSize(500, 400)

    def getSelectedDirection(self, rowNumber):
        door_id = self.table.item(rowNumber, 0).text()
        return door_id, direction

    def addButtonClicked(self):
        classobjs = [tile.LockedDoor, tile.LockedDoorWithKeypad]
        doortypes = {obj.__name__: obj for obj in classobjs}

        item, accepted = QtWidgets.QInputDialog.getItem(self,
                                                        "select door type",
                                                        "Select a door type",
                                                        doortypes, 0, False)
        if not accepted:
            return

        doortype = doortypes[item]
        if doortype == tile.LockedDoor:
            settings = forms.DoorSettings()
        else:
            settings = forms.KeypadDoorSettings()

        direction, doorobj = self.populateDoorSettings(settings, None)
        if doorobj is None:
            return

        if self.parent.tileIDExists(doorobj.tile_id):
            errorDialog(self, "Unable to create door",
                        "Tile ID '%s' is already is use!" % doorobj.tile_id)
            return

        if direction in self.directions:
            errorDialog(self, "Unable to create door",
                        "There is already a door to the %s" % direction)
            return

        self.directions[direction] = doorobj
        button = self.parent.buttonAtPosition(*self.parent.selectedPosition)

        if doortype == tile.LockedDoor:
            button.addDoors(doors=[settings.direction])
        else:
            button.addDoors(keypad_doors=[settings.direction])

        # Re-draw button
        button.update()

        setattr(self.tile, direction, doorobj)
        self.addRow(doorobj, direction)

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def editButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        direction = self.table.item(selectedRow, 2).text()
        doorobj = getattr(self.tile, direction)

        if type(doorobj) == tile.LockedDoor:
            settings = forms.DoorSettings()
        else:
            settings = forms.KeypadDoorSettings()

        new_direction, new_doorobj = self.populateDoorSettings(settings, doorobj)
        if new_doorobj is None:
            return

        old_tile_id = doorobj.tile_id if doorobj else None

        if old_tile_id != new_doorobj.tile_id:
            if self.parent.tileIDExists(new_doorobj.tile_id):
                errorDialog(self, "Unable to change door settings",
                            "Tile ID '%s' is already is use!" % new_doorobj.tile_id)

            new_doorobj.set_tile_id(new_doorobj.tile_id)
            return

        button = self.parent.buttonAtPosition(*self.parent.selectedPosition)

        if new_direction != direction:
            if new_direction in self.directions:
                errorDialog(self, "Unable to change door settings",
                            "You already have a door to the %s" % new_direction)

            # Remove connection to old door
            setattr(self.tile, direction, doorobj.replacement_tile)
            button.removeDoors(directions=[direction])
            del self.directions[direction]

            # Re-connect door in new direction
            setattr(self.tile, new_direction, new_doorobj)
            self.directions[new_direction] = new_doorobj

        if type(new_doorobj) == tile.LockedDoor:
            button.addDoors(doors=[new_direction])
        else:
            button.addDoors(keypad_doors=[new_direction])

        # Re-draw button
        button.update()

        # Re-draw door browser table
        self.populateTable()

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def deleteButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        direction = self.table.item(selectedRow, 2).text()
        doorobj = getattr(self.tile, direction)

        reply = yesNoDialog(self, "Really delete door?",
                            "Are you sure you want do delete this "
                            "door (%s)?" % doorobj.tile_id)
        if not reply:
            return

        button = self.parent.buttonAtPosition(*self.parent.selectedPosition)
        button.removeDoors([direction])
        del self.directions[direction]
        setattr(self.tile, direction, doorobj.replacement_tile)
        self.table.removeRow(selectedRow)

        # Re-draw button
        button.update()

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def addRow(self, door, direction):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(door.tile_id)
        item2 = QtWidgets.QTableWidgetItem(door.__class__.__name__)
        item3 = QtWidgets.QTableWidgetItem(direction)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)
        self.table.setItem(nextFreeRow, 2, item3)

    def getDoorSettings(self, settings_obj, window_title, tile_id):
        complete = False
        if tile_id is None:
            settings_obj.tile_id = "door%d" % self.door_id
            settings_obj.name = "door"
            settings_obj.prefix = "a"
            self.door_id += 1
        else:
            settings_obj.tile_id = tile_id

        while not complete:
            dialog = QtAutoForm(settings_obj, title=window_title,
                                formTitle="Set attributes for selected door",
                                spec=settings_obj.spec)

            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.setWindowIcon(QtGui.QIcon(self.parent.main.iconPath))
            dialog.exec_()

            # Dialog was cancelled, we're done
            if not dialog.wasAccepted():
                return False

            if str(settings_obj.tile_id).strip() == '':
                errorDialog(self, "Invalid tile ID", "tile ID field cannot be empty")

            else:
                complete = True

        return True

    def oppositeDoorExists(self, opposite_tile, direction):
        if not opposite_tile:
            return False

        opposite_dir = tile.reverse_direction(direction)
        opposite = getattr(opposite_tile, opposite_dir)
        return opposite and opposite.is_door()

    def formToInstance(self, settings, door, olddir, replace):
        if type(settings) == forms.KeypadDoorSettings:
            if door is None:
                door = tile.LockedDoorWithKeypad(settings.code, prefix=settings.prefix,
                                                name=settings.name, src_tile=self.tile,
                                                replacement_tile=replace)
            else:
                door.__class__.__init__(door, settings.code, prefix=settings.prefix,
                                        name=settings.name, src_tile=self.tile,
                                        replacement_tile=replace)

            door.set_prompt(settings.prompt)

        elif type(settings) == forms.DoorSettings:
            if door is None:
                door = tile.LockedDoor(settings.prefix, settings.name, self.tile, replace)
            else:
                door.__class__.__init__(door, settings.prefix, settings.name,
                                        self.tile, replace)

        if olddir and (olddir != settings.direction):
            setattr(self.tile, olddir, door.replacement_tile)

        return door

    def instanceToForm(self, settings, door):
        settings.direction = self.tile.direction_to(door)
        settings.prefix = door.prefix
        settings.name = door.name

        if type(door) == tile.LockedDoorWithKeypad:
            settings.code = door.unlock_code
            settings.prompt = door.prompt

    def populateDoorSettings(self, settings, doorobj):
        tile_id = None
        olddir = None

        if doorobj is not None:
            tile_id = doorobj.tile_id
            self.instanceToForm(settings, doorobj)
            olddir = settings.direction

        wasAccepted = self.getDoorSettings(settings, "Door settings", tile_id)
        if not wasAccepted:
            return None, None

        replace = getattr(self.tile, settings.direction)

        # Check if there's already a door in this direction on the adjacent tile
        if self.oppositeDoorExists(replace, settings.direction):
            errorDialog(self, "Unable to add door", "There is an existing door "
                        " locked from the opposite direction (tile ID '%s')"
                        % replace.tile_id)

            return None, None

        doorobj = self.formToInstance(settings, doorobj, olddir, replace)

        doorobj.tile_id = settings.tile_id
        return settings.direction, doorobj
