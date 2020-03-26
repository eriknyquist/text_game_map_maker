from text_game_map_maker import forms
from text_game_map_maker.qt_auto_form import QtAutoForm
from text_game_map_maker import object_builders as builders

from text_game_maker.tile import tile
from PyQt5 import QtWidgets, QtCore, QtGui


class ItemEditor(QtWidgets.QDialog):
    def __init__(self, parent, tileobj):
        super(ItemEditor, self).__init__(parent=parent)

        self.parent = parent
        self.tile = tileobj
        self.row_items = []

        self.classobjs = [builders.FoodBuilder]
        self.builders = {c.objtype.__name__: c() for c in self.classobjs}

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(['item type', 'item name', 'location'])
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
        self.addButton.setText("Add item")
        self.editButton.setText("Edit item")
        self.deleteButton.setText("Delete item")

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
        self.setWindowTitle("Item Editor")

    def populateTable(self):
        self.row_items = []

        self.table.setRowCount(0)
        for loc in self.tile.items:
            for item in self.tile.items[loc]:
                self.addRow(item)
                self.row_items.append(item)

    def sizeHint(self):
        return QtCore.QSize(500, 400)

    def getSelectedDirection(self, rowNumber):
        door_id = self.table.item(rowNumber, 0).text()
        return door_id, direction

    def addButtonClicked(self):
        item, accepted = QtWidgets.QInputDialog.getItem(self,
                                                        "select object type",
                                                        "Select an object type",
                                                        self.builders.keys(),
                                                        0, False)
        if not accepted:
            return

        builder = self.builders[item]
        instance = builder.build_instance()
        if not instance:
            return

        self.addRow(instance)
        self.row_items.append(instance)
        self.tile.add_item(instance)

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def editButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        item = self.row_items[selectedRow]
        classname = item.__class__.__name__
        builder = self.builders[classname]

        if not builder.edit_instance(item):
            return

        # Re-draw door browser table
        self.populateTable()

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def deleteButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        item = self.row_items[selectedRow]

        reply = self.parent.yesNoDialog("Really delete item?",
                                      "Are you sure you want do delete this "
                                      "item (%s)?" % item.name)
        if not reply:
            return

        item.delete()
        self.table.removeRow(selectedRow)

        # Enabling saving if it was disabled
        self.parent.setSaveEnabled(True)

    def addRow(self, item):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(item.__class__.__name__)
        item2 = QtWidgets.QTableWidgetItem(item.name)
        item3 = QtWidgets.QTableWidgetItem(item.location)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)
        self.table.setItem(nextFreeRow, 2, item3)
