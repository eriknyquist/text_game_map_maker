from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox, QDoubleSpinBox,
QTextEdit, QVBoxLayout)

import sys

_input_decoders = {
    'str': (lambda x: x.text(), lambda: QLineEdit()),
    'int': (lambda x: x.value(), lambda: QSpinBox()),
    'float': (lambda x: x.value(), lambda: QDoubleSpinBox())
}

class InputWidget(object):
    def __init__(self, instance, attr, input_getter, widget_getter):
        self.instance = instance
        self.attr = attr
        self.input_getter = input_getter
        self.widget = widget_getter()

    def writeValue(self):
        value = self.input_getter(self.widget)
        setattr(self.instance, self.attr, value)

    def rowItems(self):
        return (QLabel("%s:" % self.attr), self.widget)

class TestClass(object):
    def __init__(self):
        self.intval = 0
        self.strval = ""
        self.floatval = 0.0

def getInputWidgetForAttr(instance, attrname):
    typestr = type(getattr(instance, attrname)).__name__
    if typestr not in _input_decoders:
        typestr = 'str'

    input_getter, widget_getter = _input_decoders[typestr]
    return InputWidget(instance, attrname, input_getter, widget_getter)

class Dialog(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, instance):
        super(Dialog, self).__init__()
        self.widgets = []
        self.createFormFromInstance(instance)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.accepted.connect(self.writeInstanceValues)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Editor")

    def writeInstanceValues(self):
        for widget in self.widgets:
            widget.writeValue()

    def createFormFromInstance(self, instance):
        classname = instance.__class__.__name__
        self.formGroupBox = QGroupBox(instance.__class__.__name__)
        layout = QFormLayout()

        self.widgets = []
        for attrname in instance.__dict__:
            attr = instance.__dict__[attrname]
            input_widget = getInputWidgetForAttr(instance, attrname)
            layout.addRow(*input_widget.rowItems())
            self.widgets.append(input_widget)

        self.formGroupBox.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ins = TestClass()
    dialog = Dialog(ins)
    dialog.exec_()

    print("intval=%d, floatval=%.2f, strval=%s" % (ins.intval, ins.floatval, ins.strval))
