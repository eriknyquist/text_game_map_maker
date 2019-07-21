import sys

from map_editor import MapEditor

from PyQt5 import QtWidgets

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MapEditor()
    w.show()
    sys.exit(app.exec_())

