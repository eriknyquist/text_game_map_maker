import sys
from PyQt5 import QtWidgets, QtCore

from text_game_maker.tile.tile import Tile

from qt_auto_form import QtAutoForm

_tiles = {}

class IndicSelectWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(IndicSelectWindow, self).__init__(parent=parent)
        self.resize(500, 400)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        for i in range(100):
            for j in range(100):
                btn = QtWidgets.QPushButton()
                btn.setFixedSize(50, 50)
                btn.clicked.connect(self.onButtonClick)
                self.gridLayout.addWidget(btn, i, j)

    def onButtonClick(self):
        button = self.sender()
        idx = self.gridLayout.indexOf(button)
        location = self.gridLayout.getItemPosition(idx)[:2]

        if location not in _tiles:
            _tiles[location] = Tile()

        tile = _tiles[location]

        spec = {
            'description': 'str',
            'name': 'str',
            'tile_id': 'str',
            'first_visit_message': 'str',
            'first_visit_message_in_dark': 'bool',
            'dark': 'bool',
            'smell_description': 'str',
            'ground_smell_description': 'str',
            'ground_taste_description': 'str'
        }

        dialog = QtAutoForm(tile, spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        button.setText(tile.tile_id)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = IndicSelectWindow()
    w.show()
    sys.exit(app.exec_())
