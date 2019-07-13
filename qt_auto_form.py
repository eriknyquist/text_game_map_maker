from PyQt5.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QTextEdit, QVBoxLayout, QCheckBox)

import sys

_input_decoders = {
    'str': (lambda x: x.text(), lambda x, y: x.setText(y), lambda: QLineEdit()),
    'int': (lambda x: x.value(), lambda x, y: x.setValue(y), lambda: QSpinBox()),
    'float': (lambda x: x.value(), lambda x, y: x.setValue(y), lambda: QDoubleSpinBox()),
    'bool': (lambda x: x.isChecked(), lambda x, y: x.setChecked(y), lambda: QCheckBox())
}

class InputWidget(object):
    def __init__(self, instance, attr, value_getter, value_setter, widget_getter):
        self.instance = instance
        self.attr = attr
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.widget = widget_getter()

    def setInstanceValue(self):
        value = self.value_getter(self.widget)
        setattr(self.instance, self.attr, value)

    def setWidgetValue(self, value):
        value = getattr(self.instance, self.attr)
        self.value_setter(self.widget, value)

    def rowItems(self):
        return (QLabel("%s:" % self.attr), self.widget)

class TestClass(object):
    def __init__(self):
        self.intval = 26
        self.strval = "ditpojid"
        self.floatval = 0.454
        self.boolval = False

def getInputWidgetForAttr(instance, attrname):
    typestr = type(getattr(instance, attrname)).__name__
    if typestr not in _input_decoders:
        typestr = 'str'

    value_getter, value_setter, widget_getter = _input_decoders[typestr]
    return InputWidget(instance, attrname, value_getter, value_setter, widget_getter)

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
            widget.setInstanceValue()

    def createFormFromInstance(self, instance):
        classname = instance.__class__.__name__
        self.formGroupBox = QGroupBox(instance.__class__.__name__)
        layout = QFormLayout()

        self.widgets = []
        for attrname in instance.__dict__:
            input_widget = getInputWidgetForAttr(instance, attrname)
            input_widget.setWidgetValue(instance.__dict__[attrname])
            layout.addRow(*input_widget.rowItems())
            self.widgets.append(input_widget)

        self.formGroupBox.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ins = TestClass()
    dialog = Dialog(ins)
    dialog.exec_()

    print("intval=%d, floatval=%.2f, strval=%s, boolval=%s" % (ins.intval, ins.floatval, ins.strval, ins.boolval))
