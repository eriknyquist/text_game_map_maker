import sys
import os

from map_builder_gui.map_editor import MapEditor

from PyQt5 import QtWidgets, QtGui, QtCore

from map_builder_gui import __maintainer__ as package_author
from map_builder_gui import __email__ as author_email
from map_builder_gui import __name__ as package_name
from map_builder_gui import __version__ as package_version


class TextDisplayWindow(QtWidgets.QDialog):
    def __init__(self, title, text):
        super(TextDisplayWindow, self).__init__()

        self.setMinimumSize(QtCore.QSize(440, 240))
        self.setWindowTitle(title)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.textField = QtWidgets.QPlainTextEdit(self)
        self.textField.insertPlainText(text)
        self.textField.setReadOnly(True)

        self.mainLayout.addWidget(self.textField)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUi()

    def initUi(self):
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.iconPath = os.path.join(scriptDir, 'images', 'logo.png')
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        self.widget = MapEditor(mainWindow=self)
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
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.loadGameAction)

        editMenu = menu.addMenu("Edit")
        editMenu.addAction(self.editTileAction)
        editMenu.addAction(self.deleteTileAction)
        editMenu.addAction(self.editDoorsAction)

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

        msgBox = TextDisplayWindow("About", "\n".join(lines))
        msgBox.setWindowIcon(QtGui.QIcon(self.iconPath))
        msgBox.exec_()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

