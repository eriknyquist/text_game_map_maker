from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_map_maker.utils import yesNoDialog
from text_game_map_maker.constants import available_item_sizes
from text_game_map_maker.qt_auto_form import QtAutoForm
from text_game_map_maker import object_builders as builders
from text_game_map_maker import saved_objects, utils

from text_game_maker.game_objects.items import ItemSize


# ----- QtAutoForm subclasses -----

class ItemEditorAutoForm(QtAutoForm):
    def getAttribute(self, attrname):
        if attrname == 'size':
            val = getattr(self.instance, attrname)
            for s in available_item_sizes:
                if getattr(ItemSize, s) == val:
                    return s

        return getattr(self.instance, attrname)

    def setAttribute(self, attrname, value):
        if attrname == 'size':
            setattr(self.instance, attrname, getattr(ItemSize, value))
            return

        setattr(self.instance, attrname, value)


class ContainerItemEditorAutoForm(ItemEditorAutoForm):
    def __init__(self, *args, **kwargs):
        QtAutoForm.__init__(self, *args, **kwargs, extra_button=True,
                            extra_button_text="contained items...")

    def extraButtonClicked(self):
        dialog = ContainerItemBrowser(self, self.instance)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()


class BlueprintItemEditorAutoForm(ItemEditorAutoForm):
    def __init__(self, *args, **kwargs):
        QtAutoForm.__init__(self, *args, **kwargs, extra_button=True,
                            extra_button_text="ingredients...")

    def extraButtonClicked(self):
        dialog = BlueprintItemBrowser(self, self.instance)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()


class ItemBrowser(QtWidgets.QDialog):
    """
    Abstract implementation of class to browse items contained within another item
    """

    def __init__(self, parent, container):
        super(ItemBrowser, self).__init__(parent=parent)

        self.parent = parent
        self.container = container
        self.row_items = []

        self.classobjs = [
            builders.FoodBuilder,
            builders.ItemBuilder,
            builders.FlashlightBuilder,
            builders.BatteryBuilder,
            builders.CoinsBuilder,
            builders.PaperBagBuilder,
            builders.SmallBagBuilder,
            builders.BagBuilder,
            builders.LargeBagBuilder,
            builders.SmallTinBuilder,
            builders.LighterBuilder,
            builders.BoxOfMatchesBuilder,
            builders.LockpickBuilder,
            builders.StrongLockpickBuilder,
            builders.ContainerBuilder,
            builders.LargeContainerBuilder,
            builders.FurnitureBuilder,
            builders.BlueprintBuilder
        ]

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
        self.savedItemButton = QtWidgets.QPushButton()
        self.saveButton = QtWidgets.QPushButton()
        self.editButton = QtWidgets.QPushButton()
        self.deleteButton = QtWidgets.QPushButton()
        self.addButton.setText("Add item")
        self.savedItemButton.setText("Add saved")
        self.saveButton.setText("Save item")
        self.editButton.setText("Edit item")
        self.deleteButton.setText("Delete item")

        self.editButton.clicked.connect(self.editButtonClicked)
        self.savedItemButton.clicked.connect(self.savedItemButtonClicked)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.addButton.clicked.connect(self.addButtonClicked)
        self.deleteButton.clicked.connect(self.deleteButtonClicked)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.editButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addWidget(self.savedItemButton)
        buttonLayout.addWidget(self.saveButton)
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

    def sizeHint(self):
        return QtCore.QSize(500, 400)

    def savedItemButtonClicked(self):
        object_names = saved_objects.get_object_names()
        if len(object_names) == 0:
            utils.infoDialog(self, message="No saved objects added yet")
            return

        name, accepted = QtWidgets.QInputDialog.getItem(self,
                                                        "select saved object",
                                                        "Select a saved object",
                                                        saved_objects.get_object_names(),
                                                        0, False)
        if not accepted:
            return

        item = saved_objects.get_object_by_name(name)
        self.addRow(item)
        self.row_items.append(item)
        self.addItemToContainer(item)

    def saveButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        item = self.row_items[selectedRow]
        saved_objects.save_object(item)
        utils.infoDialog(self, message="Object '%s' saved successfully" % item.name)

    def addButtonClicked(self):
        item, accepted = QtWidgets.QInputDialog.getItem(self,
                                                        "select object type",
                                                        "Select an object type",
                                                        self.builders.keys(),
                                                        0, False)
        if not accepted:
            return

        builder = self.builders[item]
        if builder.__class__ == builders.BlueprintBuilder:
            form = BlueprintItemEditorAutoForm
        else:
            form = ContainerItemEditorAutoForm

        instance = builder.build_instance(formclass=form)
        if not instance:
            return

        self.addRow(instance)
        self.row_items.append(instance)
        self.addItemToContainer(instance)

    def editButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        item = self.row_items[selectedRow]
        classname = item.__class__.__name__
        builder = self.builders[classname]

        if builder.__class__ == builders.BlueprintBuilder:
            form = BlueprintItemEditorAutoForm
        else:
            form = ContainerItemEditorAutoForm

        if not builder.edit_instance(item, formclass=form):
            return

        # Re-draw door browser table
        self.populateTable()

    def deleteButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return

        item = self.row_items[selectedRow]

        reply = yesNoDialog(self, "Really delete item?",
                            "Are you sure you want do delete this item (%s)?" % item.name)
        if not reply:
            return

        self.deleteItemFromContainer(item)
        item.delete()
        self.table.removeRow(selectedRow)
        self.populateTable()

    def addRow(self, item):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        clsname, name, loc = self.getRowInfo(item)
        item1 = QtWidgets.QTableWidgetItem(clsname)
        item2 = QtWidgets.QTableWidgetItem(name)
        item3 = QtWidgets.QTableWidgetItem(loc)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)
        self.table.setItem(nextFreeRow, 2, item3)

    def deleteItemFromContainer(self, item):
        pass

    def getRowInfo(self, item):
        raise NotImplementedError()

    def addItemToContainer(self, item):
        raise NotImplementedError()

    def populateTable(self):
        raise NotImplementedError()


# ----- ItemBrowser subclasses -----

class TileItemBrowser(ItemBrowser):
    """
    Concrete item browser implementation to browse items contained in a Tile object
    """

    def populateTable(self):
        self.row_items = []

        self.table.setRowCount(0)
        for loc in self.container.items:
            for item in self.container.items[loc]:
                self.addRow(item)
                self.row_items.append(item)

    def addItemToContainer(self, item):
        self.container.add_item(item)

    def getRowInfo(self, item):
        return item.__class__.__name__, item.name, item.location


class ContainerItemBrowser(ItemBrowser):
    """
    Concrete item browser implementation to browse items contained in another item
    """

    def populateTable(self):
        self.row_items = []

        self.table.setRowCount(0)
        for item in self.container.items:
            self.addRow(item)
            self.row_items.append(item)

    def addItemToContainer(self, item):
        self.container.add_item(item)

    def getRowInfo(self, item):
        loc = 'inside %s' % self.container.__class__.__name__
        return item.__class__.__name__, item.name, loc


class BlueprintItemBrowser(ItemBrowser):
    """
    Concrete item browser implementation to browse ingredient items in a Blueprint
    """

    def populateTable(self):
        self.row_items = []

        self.table.setRowCount(0)
        for item in self.container.ingredients:
            self.addRow(item)
            self.row_items.append(item)

    def addItemToContainer(self, item):
        self.container.ingredients.append(item)

    def getRowInfo(self, item):
        return item.__class__.__name__, item.name, item.location


class SavedItemBrowser(ItemBrowser):
    """
    Concrete item browser implementation to browse custom objects saved for re-use
    """

    def populateTable(self):
        self.row_items = []

        self.table.setRowCount(0)
        saved_objs = saved_objects.get_objects()
        for name in saved_objs:
            self.addRow(saved_objs[name])
            self.row_items.append(saved_objs[name])

    def addItemToContainer(self, item):
        saved_objects.save_object(item)

    def getRowInfo(self, item):
        return item.__class__.__name__, item.name, "Saved objects database"

    def deleteItemFromContainer(self, item):
        saved_objects.delete_object(item)
