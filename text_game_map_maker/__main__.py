import sys
import os

from text_game_map_maker.map_editor import MapEditor

from PyQt5 import QtWidgets, QtGui, QtCore

from text_game_map_maker import __maintainer__ as package_author
from text_game_map_maker import __email__ as author_email
from text_game_map_maker import __name__ as package_name
from text_game_map_maker import __version__ as package_version

try:
    from text_game_map_maker import git_rev
except ImportError:
    # No git_rev.py created yet, unreleased version
    git_commit = "dev"
else:
    git_commit = git_rev.commit[:7]


def textDisplayWindow(title, message):
    msg = QtWidgets.QMessageBox()
    msg.setInformativeText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, primary_screen):
        super(MainWindow, self).__init__()

        self.primary_screen = primary_screen
        self.initUi()

    def initUi(self):
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        imageDir = os.path.join(scriptDir, 'images')
        self.iconPath = os.path.join(imageDir, 'logo.png')
        self.compassPath = os.path.join(imageDir, 'compass.png')
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        self.widget = MapEditor(self.primary_screen, self)
        self.setCentralWidget(self.widget)

        # File menu actions
        self.openAction = QtWidgets.QAction("Open", self)
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.setStatusTip("Open saved file")
        self.openAction.triggered.connect(self.widget.loadButtonClicked)

        self.saveAction = QtWidgets.QAction("Save", self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.setStatusTip("Save to file")
        self.saveAction.triggered.connect(self.widget.saveButtonClicked)

        self.saveAsAction = QtWidgets.QAction("Save As", self)
        self.saveAsAction.setShortcut("Ctrl+A")
        self.saveAsAction.setStatusTip("Save to file, always pick the file first")
        self.saveAsAction.triggered.connect(self.widget.saveAsButtonClicked)

        self.loadGameAction = QtWidgets.QAction("Load map from saved game file", self)
        self.loadGameAction.setShortcut("Ctrl+G")
        self.loadGameAction.setStatusTip("Load the map data from saved game file")
        self.loadGameAction.triggered.connect(self.widget.loadFromSavedGameButtonClicked)

        # Edit menu actions
        self.editTileAction = QtWidgets.QAction("Edit selected tile", self)
        self.editTileAction.setShortcut("Ctrl+E")
        self.editTileAction.setStatusTip("Set/change attributes for selected tile")
        self.editTileAction.triggered.connect(self.widget.editSelectedTile)

        self.editDoorsAction = QtWidgets.QAction("Edit doors on selected tile", self)
        self.editDoorsAction.setShortcut("Ctrl+D")
        self.editDoorsAction.setStatusTip("Add/edit doors on selected tile")
        self.editDoorsAction.triggered.connect(self.widget.doorButtonClicked)

        self.editWallsAction = QtWidgets.QAction("Edit walls on selected tile", self)
        self.editWallsAction.setShortcut("Ctrl+W")
        self.editWallsAction.setStatusTip("Add/edit walls on selected tile")
        self.editWallsAction.triggered.connect(self.widget.wallButtonClicked)

        self.editItemsAction = QtWidgets.QAction("Edit items on selected tile", self)
        self.editItemsAction.setShortcut("Ctrl+I")
        self.editItemsAction.setStatusTip("Add/edit items on selected tile")
        self.editItemsAction.triggered.connect(self.widget.itemButtonClicked)

        self.deleteTileAction = QtWidgets.QAction("Delete selected tiles", self)
        self.deleteTileAction.setShortcut("Ctrl+R")
        self.deleteTileAction.setStatusTip("Delete selected tiles")
        self.deleteTileAction.triggered.connect(self.widget.deleteButtonClicked)

        self.clearAction = QtWidgets.QAction("Clear all tiles", self)
        self.clearAction.setShortcut("Ctrl+X")
        self.clearAction.setStatusTip("Clear all tiles")
        self.clearAction.triggered.connect(self.widget.clearButtonClicked)

        self.copyTileAction = QtWidgets.QAction("Copy selected tiles", self)
        self.copyTileAction.setShortcut("Ctrl+C")
        self.copyTileAction.setStatusTip("Copy selected tiles")
        self.copyTileAction.triggered.connect(self.widget.copyButtonClicked)

        self.moveTileAction = QtWidgets.QAction("Move selected tiles", self)
        self.moveTileAction.setShortcut("Ctrl+M")
        self.moveTileAction.setStatusTip("Move selected tiles")
        self.moveTileAction.triggered.connect(self.widget.moveButtonClicked)

        self.startTileAction = QtWidgets.QAction("Set selected tile as start tile", self)
        self.startTileAction.setShortcut("Ctrl+T")
        self.startTileAction.setStatusTip("Set start tile")
        self.startTileAction.triggered.connect(self.widget.setStartTile)

        # View  menu actions
        self.zoomInAction = QtWidgets.QAction("Zoom in", self)
        self.zoomInAction.setShortcut("=")
        self.zoomInAction.setStatusTip("Increase magnification level of tile grid view")
        self.zoomInAction.triggered.connect(self.widget.increaseZoomLevel)

        self.zoomOutAction = QtWidgets.QAction("Zoom out", self)
        self.zoomOutAction.setShortcut("-")
        self.zoomOutAction.setStatusTip("Decrease magnification level of tile grid view")
        self.zoomOutAction.triggered.connect(self.widget.decreaseZoomLevel)

        self.zoomResetAction = QtWidgets.QAction("Reset Zoom", self)
        self.zoomResetAction.setShortcut("Ctrl+=")
        self.zoomResetAction.setStatusTip("Reset magnification level of tile grid view to default")
        self.zoomResetAction.triggered.connect(self.widget.setDefaultZoomLevel)

        # Help menu actions
        self.aboutAction = QtWidgets.QAction("About", self)
        self.aboutAction.triggered.connect(self.showAboutWindow)

        self.howToAction = QtWidgets.QAction("Help!", self)
        self.howToAction.triggered.connect(self.showHowToWindow)

        # Build menu bar
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.loadGameAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)

        editMenu = menu.addMenu("Edit")
        editMenu.addAction(self.editTileAction)
        editMenu.addAction(self.editDoorsAction)
        editMenu.addAction(self.editWallsAction)
        editMenu.addAction(self.editItemsAction)
        editMenu.addAction(self.startTileAction)

        toolMenu = menu.addMenu("Tools")
        toolMenu.addAction(self.moveTileAction)
        toolMenu.addAction(self.copyTileAction)
        toolMenu.addAction(self.deleteTileAction)
        toolMenu.addAction(self.clearAction)

        viewMenu = menu.addMenu("View")
        viewMenu.addAction(self.zoomInAction)
        viewMenu.addAction(self.zoomOutAction)
        viewMenu.addAction(self.zoomResetAction)

        helpMenu = menu.addMenu("Help")
        helpMenu.addAction(self.aboutAction)
        helpMenu.addAction(self.howToAction)

        # Set initial selection position
        self.widget.setSelectedPosition(self.widget.buttonAtPosition(0, 0))

        # Saving is disabled initially
        self.widget.setSaveEnabled(False)

        self.widget.enableSelectionDependentItems()

    def closeEvent(self, event):
        if self.widget.warningBeforeQuit():
            event.accept()
        else:
            event.ignore()

    def showHowToWindow(self):
        lines = [
            "How to use %s\n\n" % package_name,
            "The main window of the application shows a large grid of squares, ",
            "which represents your entire game world. Each square represents a ",
            "distinct area within the game (referred to as a 'tile'), which the ",
            "player can travel between using the normal movement commands ",
            "during gameplay (e.g. 'go north', 'travel west').\n\n",
            "Left-click on a square to create a new tile or edit the attributes ",
            "of an existing tile. Right click on a square to select it without ",
            "opening the tile editor window.\n\n",
            "You can also use the arrow keys to change the selected tile, and ",
            "the Enter key to create/edit the currently selected tile.\n\n",
            "Tiles created next to each other will be automatically connected ",
            "(i.e. the player can move freely between them), but you can use "
            "the buttons in the toolbar to add walls or doors between adjacent ",
            "tiles.",
        ]

        textDisplayWindow("How to use %s" % package_name, "".join(lines))

    def showAboutWindow(self):
        lines = [
            "%s is a tool for creating maps that can be loaded and " % package_name,
            "used with the text_game_maker python library.\n\n",
            "author: %s (%s)\n\n" % (package_author, author_email),
            "version: %s (%s)\n\n" % (package_version, git_commit),
            "https://github.com/eriknyquist/text_game_maker\n\n",
            "https://github.com/eriknyquist/text_game_map_maker"
        ]

        textDisplayWindow("About %s" % package_name, "".join(lines))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(app.primaryScreen())
    win.setWindowTitle("%s %s" % (package_name, package_version))
    win.show()
    sys.exit(app.exec_())

