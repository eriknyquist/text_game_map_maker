import sys
import os

from text_game_map_maker.map_editor import MapEditor

from PyQt5 import QtWidgets, QtGui, QtCore

from text_game_map_maker import __maintainer__ as package_author
from text_game_map_maker import __email__ as author_email
from text_game_map_maker import __name__ as package_name
from text_game_map_maker import __version__ as package_version


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
        self.iconPath = os.path.join(scriptDir, 'images', 'logo.png')
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

        self.deleteTileAction = QtWidgets.QAction("Delete selected tile", self)
        self.deleteTileAction.setShortcut("Ctrl+R")
        self.deleteTileAction.setStatusTip("Delete selected tile")
        self.deleteTileAction.triggered.connect(self.widget.deleteButtonClicked)

        # Help menu actions
        self.aboutAction = QtWidgets.QAction("About", self)
        self.aboutAction.triggered.connect(self.showAboutWindow)

        # Build menu bar
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.loadGameAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)

        editMenu = menu.addMenu("Edit")
        editMenu.addAction(self.editTileAction)
        editMenu.addAction(self.deleteTileAction)
        editMenu.addAction(self.editDoorsAction)
        editMenu.addAction(self.editWallsAction)

        helpMenu = menu.addMenu("Help")
        helpMenu.addAction(self.aboutAction)

        # Set initial selection position
        self.widget.setSelectedPosition(self.widget.buttonAtPosition(0, 0))

        # Saving is disabled initially
        self.widget.setSaveEnabled(False)

    def showAboutWindow(self):
        lines = [
            "%s is a tool for creating maps that can be loaded and" % package_name,
            "used with the text_game_maker package.\n",
            "text_game_maker: https://github.com/eriknyquist/text_game_maker\n",
            "author: %s (%s)\n" % (package_author, author_email),
            "version: %s" % (package_version)
        ]

        textDisplayWindow("About %s" % package_name, "\n".join(lines))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(app.primaryScreen())
    win.setWindowTitle("%s %s" % (package_name, package_version))
    win.show()
    sys.exit(app.exec_())
