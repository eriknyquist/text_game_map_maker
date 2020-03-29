from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QComboBox, QPlainTextEdit,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QTextEdit, QVBoxLayout, QCheckBox, QSizePolicy,
    QScrollArea, QWidget, QPushButton)

from PyQt5 import QtCore


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

def _combo_box_set_text(combo, text):
    index = combo.findText(text, QtCore.Qt.MatchFixedString)
    if index >= 0:
        combo.setCurrentIndex(index)

def _plain_text_edit():
    w = QPlainTextEdit()
    w.setTabChangesFocus(True)
    return w

_input_decoders = {
    'str': (
        lambda x: x.text(),
        lambda x, y: x.setText(y),
        lambda: QLineEdit(),
        ''),
    'long_str': (
        lambda x: x.toPlainText(),
        lambda x, y: x.insertPlainText(y),
        _plain_text_edit,
        ''),
    'int': (
        lambda x: x.value(),
        lambda x, y: x.setValue(y),
        _spin_box,
        0),
    'float': (
        lambda x: x.value(),
        lambda x, y: x.setValue(y),
        _double_spin_box,
        0.0),
    'bool': (
        lambda x: x.isChecked(),
        lambda x, y: x.setChecked(y),
        lambda: QCheckBox(),
        False),
    'choice': (
        lambda x: x.currentText(),
        _combo_box_set_text,
        lambda: QComboBox(),
        '')
}

class InputWidget(object):
    def __init__(self, instance, attr, typename, value_getter, value_setter,
                 widget_getter, default_value, label, tooltip=None):
        self.instance = instance
        self.attr = attr
        self.typename = typename
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.widget = widget_getter()
        self.label = QLabel("%s:" % label)
        self.default_value = default_value

        if tooltip is not None:
            self.widget.setToolTip(tooltip)
            self.label.setToolTip(tooltip)

    def getWidgetValue(self):
        value = self.value_getter(self.widget)

        try:
            cast_value = eval(self.typename)(value)
        except Exception:
            value = str(value)
        else:
            value = cast_value

        return value

    def setWidgetValue(self, value):
        if self.typename != "choice":
            if value is None:
                value = self.default_value
            else:
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
    tooltip = None
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
        if "tooltip" in attrs:
            tooltip = attrs["tooltip"]

    value_getter, value_setter, widget_getter, default = _input_decoders[typename]

    widget = InputWidget(instance, attrname, typename, value_getter, value_setter,
                         widget_getter, default, label, tooltip)

    if widget.typename == "choice":
        if "choices" in attrs:
            widget.widget.addItems(attrs["choices"])

    return widget

class QtAutoForm(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, instance, title=None, spec=None, formTitle=None,
                 scrollable=False, headerText=None, extra_button=False,
                 extra_button_text=""):
        super(QtAutoForm, self).__init__()

        if formTitle is None:
            self.form_title = instance.__class__.__name__
        else:
            self.form_title = formTitle

        self.instance = None
        self.spec = spec
        self.widgets = []
        self.extra_button = extra_button

        self.extraButton = QPushButton(extra_button_text)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        if extra_button:
            self.extraButton.clicked.connect(self.extraButtonClicked)
            buttonBox.addButton(self.extraButton, QDialogButtonBox.ActionRole)

        self.accepted.connect(self.writeInstanceValues)

        self.formGroupBox = QGroupBox(self.form_title)

        if scrollable:
            self.scrollArea = QScrollArea()
            self.scrollArea.setWidgetResizable(True)
            self.scrollArea.setWidget(self.formGroupBox)
            mainWidget = self.scrollArea
        else:
            mainWidget = self.formGroupBox

        mainLayout = QVBoxLayout()

        if headerText is not None:
            label = QLabel(headerText, self)
            label.setWordWrap(True)
            mainLayout.addWidget(label)

        mainLayout.addWidget(mainWidget)
        mainLayout.addWidget(buttonBox)

        self.setLayout(mainLayout)
        self.setWindowTitle("Editor" if title is None else title)
        self.accepted = False

        self.createFormFromInstance(instance)

    def writeInstanceValues(self):
        for widget in self.widgets:
            self.setAttribute(widget.attr, widget.getWidgetValue())

        self.accepted = True

    def wasAccepted(self):
        return self.accepted

    def createFormFromInstance(self, instance):
        self.instance = instance
        classname = instance.__class__.__name__
        layout = QFormLayout()

        self.widgets = []
        for attrname in self.spec:
            input_widget = getInputWidgetForAttr(instance, attrname, self.spec)

            attrvalue = self.getAttribute(attrname)
            if attrvalue is None:
                widgetvalue = input_widget.default_value
            else:
                widgetvalue = attrvalue

            input_widget.setWidgetValue(widgetvalue)
            layout.addRow(*input_widget.rowItems())
            self.widgets.append(input_widget)

        self.formGroupBox.setLayout(layout)

    def getAttribute(self, attrname):
        return getattr(self.instance, attrname)

    def setAttribute(self, attrname, value):
        setattr(self.instance, attrname, value)

    def extraButtonClicked(self):
        pass
