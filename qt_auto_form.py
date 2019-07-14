from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QComboBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QTextEdit, QVBoxLayout, QCheckBox, QSizePolicy)

def _spin_box():
    w = QSpinBox()
    w.setMaximum((2 ** 31) - 1)
    w.setMinimum(-(2 ** 31) + 1)
    return w

def _double_spin_box():
    w = QDoubleSpinBox()
    w.setMaximum(float(2 ** 31) - 1.0)
    w.setMinimum(float(-(2 ** 31)) + 1.0)
    return w

_input_decoders = {
    'str': (lambda x: x.text(), lambda x, y: x.setText(y), lambda: QLineEdit()),
    'int': (lambda x: x.value(), lambda x, y: x.setValue(y), _spin_box),
    'float': (lambda x: x.value(), lambda x, y: x.setValue(y), _double_spin_box),
    'bool': (lambda x: x.isChecked(), lambda x, y: x.setChecked(y), lambda: QCheckBox()),
    'choice': (lambda x: x.currentText(), lambda x, y: None, lambda: QComboBox())
}

class InputWidget(object):
    def __init__(self, instance, attr, typename, value_getter, value_setter,
                 widget_getter, label):
        self.instance = instance
        self.attr = attr
        self.typename = typename
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.widget = widget_getter()
        self.label = QLabel("%s:" % label)

    def setInstanceValue(self):
        value = self.value_getter(self.widget)

        try:
            cast_value = eval(self.typename)(value)
        except Exception:
            value = str(value)
        else:
            value = cast_value

        setattr(self.instance, self.attr, value)

    def setWidgetValue(self, value):
        if self.typename == "choice":
            return

        value = getattr(self.instance, self.attr)

        try:
            cast_value = eval(self.typename)(value)
        except Exception:
            value = str(value)
        else:
            value = cast_value

        self.value_setter(self.widget, value)

    def rowItems(self):
        return self.label, self.widget

def getInputWidgetForAttr(instance, attrname, spec):
    typename = 'str'
    label = attrname
    attrs = {}

    if (spec is None) or (attrname not in spec):
        attrtype = type(getattr(instance, attrname)).__name__
        if attrtype in _input_decoders:
            typename = attrtype
    else:
        attrs = spec[attrname]
        if "type" in attrs:
            typename = attrs["type"]
        if "label" in attrs:
            label = attrs["label"]

    value_getter, value_setter, widget_getter = _input_decoders[typename]

    widget = InputWidget(instance, attrname, typename, value_getter, value_setter,
                         widget_getter, label)

    if widget.typename == "choice":
        if "choices" in attrs:
            widget.widget.addItems(attrs["choices"])

    return widget

class QtAutoForm(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, instance, title=None, spec=None):
        super(QtAutoForm, self).__init__()

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
        self.setWindowTitle("Editor" if title is None else title)
        self.accepted = False

    def writeInstanceValues(self):
        for widget in self.widgets:
            widget.setInstanceValue()

        self.accepted = True

    def wasAccepted(self):
        return self.accepted

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
