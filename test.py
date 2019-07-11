from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox, QDoubleSpinBox,
QTextEdit, QVBoxLayout)

import sys

class TestClass(object):
    def __init__(self):
        self.intval = 0
        self.strval = ""
        self.floatval = 0.0

def getInputWidgetForAttr(attrname, attr):
    if type(attr) == str:
        return QLineEdit()
    elif type(attr) == int:
        return QSpinBox()
    elif type(attr) == float:
        return QDoubleSpinBox()

    return QLineEdit()

class Dialog(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, instance):
        super(Dialog, self).__init__()
        self.createFormFromInstance(instance)
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        
        self.setWindowTitle("Editor")
        
    def createFormFromInstance(self, instance):
        classname = instance.__class__.__name__
        self.formGroupBox = QGroupBox(instance.__class__.__name__)
        layout = QFormLayout()
        for attrname in instance.__dict__:
            attr = instance.__dict__[attrname]
            input_widget = getInputWidgetForAttr(attrname, attr)
            layout.addRow(QLabel("%s:" % attrname), input_widget)

        self.formGroupBox.setLayout(layout)

    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox("Form layout")
        layout = QFormLayout()
        layout.addRow(QLabel("Name:"), QLineEdit())
        layout.addRow(QLabel("Country:"), QComboBox())
        layout.addRow(QLabel("Age:"), QSpinBox())
        self.formGroupBox.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = Dialog(TestClass())
    sys.exit(dialog.exec_())
