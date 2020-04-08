import queue
import threading

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_maker.builder.map_builder import StopWaitingForInput, clear_instance
from text_game_maker.utils import utils
from text_game_maker.utils.runner import MapRunner, run_map_from_class


class GameTerminal(QtWidgets.QDialog):
    def __init__(self, parent, map_data):
        super(GameTerminal, self).__init__(parent)

        self.inputWidget = QtWidgets.QLineEdit()
        self.outputWidget = QtWidgets.QTextEdit()
        self.outputWidget.setReadOnly(True)
        self.outputWidget.setFont(QtGui.QFont("Courier", 12))

        self.inputButton = QtWidgets.QPushButton()
        self.inputButton.setText("submit")
        self.inputButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                       QtWidgets.QSizePolicy.Preferred)
        self.inputButton.clicked.connect(self.inputButtonClicked)

        inputLayout = QtWidgets.QHBoxLayout()
        inputLayout.addWidget(self.inputWidget)
        inputLayout.addWidget(self.inputButton)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.outputWidget)
        mainLayout.addLayout(inputLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("Game Terminal")

        utils.set_printfunc(self.game_terminal_printfunc)
        utils.set_inputfunc(self.game_terminal_inputfunc)

        self.inputQueue = queue.Queue()
        self.game_thread = threading.Thread(target=self.run_game, args=(map_data,))
        self.game_thread.daemon = False
        self.game_thread.start()

    def closeEvent(self, event):
        self.inputQueue.put(StopWaitingForInput())
        clear_instance()
        self.game_thread.join()
        event.accept()

    def inputButtonClicked(self):
        text = self.inputWidget.text()
        self.inputQueue.put(text)
        self.inputWidget.clear()
        self.game_terminal_printfunc("(%s)" % text)

    def run_game(self, map_data):
        class GameTerminalMapRunner(MapRunner):
            def build_map(self, builder):
                builder.load_map_data_from_string(map_data)
                builder.set_input_prompt("")

        run_map_from_class(GameTerminalMapRunner)

    def game_terminal_inputfunc(self, prompt):
        self.game_terminal_printfunc("> ")
        return self.inputQueue.get()

    def game_terminal_printfunc(self, text):
        self.outputWidget.append(text)
        self.outputWidget.ensureCursorVisible()

    def sizeHint(self):
        return QtCore.QSize(800, 600)
