from PyQt5.QtWidgets import (QDialog, QDialogButtonBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QTextEdit, QVBoxLayout, QCheckBox, QSizePolicy)

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
        self.label = QLabel("%s:" % self.attr)

    def setInstanceValue(self):
        value = self.value_getter(self.widget)
        setattr(self.instance, self.attr, value)

    def setWidgetValue(self, value):
        value = getattr(self.instance, self.attr)
        self.value_setter(self.widget, value)

    def rowItems(self):
        return self.label, self.widget

def getInputWidgetForAttr(instance, attrname, spec):
    if (spec is None) or (attrname not in spec):
        typename = type(getattr(instance, attrname)).__name__
        if typename not in _input_decoders:
            typename = 'str'
    else:
        typename = spec[attrname]

    value_getter, value_setter, widget_getter = _input_decoders[typename]
    return InputWidget(instance, attrname, value_getter, value_setter, widget_getter)

class QtAutoForm(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, instance, spec=None):
        super(QtAutoForm, self).__init__()

        if spec is not None:
            for typename in spec.values():
                if typename not in _input_decoders:
                    raise ValueError("unknown type in spec: %s" % typename)

        self.spec = spec
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
            if (self.spec is not None) and (attrname not in self.spec):
                continue

            input_widget = getInputWidgetForAttr(instance, attrname, self.spec)

            input_widget.setWidgetValue(instance.__dict__[attrname])
            layout.addRow(*input_widget.rowItems())
            self.widgets.append(input_widget)

        self.formGroupBox.setLayout(layout)
