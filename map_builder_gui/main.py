import sys
import os

from map_editor import MapEditor

from PyQt5 import QtWidgets, QtGui

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUi()

    def initUi(self):
        self.widget = MapEditor(mainWindow=self)
        self.setCentralWidget(self.widget)

        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.iconPath = os.path.join(scriptDir, 'images', 'logo.png')
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        openAction = QtWidgets.QAction("Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open saved file")
        openAction.triggered.connect(self.widget.loadButtonClicked)

        saveAction = QtWidgets.QAction("Save", self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save to file")
        saveAction.triggered.connect(self.widget.saveButtonClicked)

        saveAsAction = QtWidgets.QAction("Save As", self)
        saveAsAction.setShortcut("Ctrl+A")
        saveAsAction.setStatusTip("Save to file, always pick the file first")
        saveAsAction.triggered.connect(self.widget.saveAsButtonClicked)

        loadGameAction = QtWidgets.QAction("Load map from saved game file", self)
        loadGameAction.setShortcut("Ctrl+G")
        loadGameAction.setStatusTip("Load the map data from saved game file")
        loadGameAction.triggered.connect(self.widget.loadFromSavedGameButtonClicked)

        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadGameAction)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

