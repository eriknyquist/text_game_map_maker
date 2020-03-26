from collections import OrderedDict

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_map_maker.qt_auto_form import QtAutoForm

from text_game_maker.materials import materials
from text_game_maker.game_objects.items import Item, Food


class ObjectBuilder(object):
    objtype = None
    spec = None

    def __init__(self):
        self.title = "%s editor" % self.__class__.objtype.__name__

    def build_instance(self):
        ins = self.__class__.objtype()
        dialog = QtAutoForm(ins, title="editor", formTitle=self.title,
                            scrollable=True, spec=self.__class__.spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        if not dialog.wasAccepted():
            return None

        self.process_dialog_settings(ins)
        return ins

    def edit_instance(self, ins):
        dialog = QtAutoForm(ins, title="editor", formTitle=self.title,
                            scrollable=True, spec=self.__class__.spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        self.process_dialog_settings(ins)
        return dialog.wasAccepted()

    def process_dialog_settings(self, ins):
        """
        Can be overridden by subclasses to transform any values set in the
        object editor dialog if needed
        """
        pass


class ItemBuilder(ObjectBuilder):
    objtype = Item
    spec = OrderedDict([
        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"}),
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),
        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),
        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                      "'on the floor' or 'hanging from the wall'"}),
        ("edible", {"type": "bool", "tooltip": "defines whether player can eat "
                    "this item without taking damage"}),
        ("combustible", {"type": "bool", "tooltip": "defines whether this item "
                         "will burn"}),
        ("energy", {"type": "int", "tooltip": "defines health gained by player "
                            "from eating this item (if edible)"}),
        ("damage", {"type": "int", "tooltip": "defines health lost by player "
                            "if damaged by this item"}),
        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                            "from selling this item"})
    ])


class FoodBuilder(ObjectBuilder):
    objtype = Food
    spec = OrderedDict([
        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"}),
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),
        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),
        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                      "'on the floor' or 'hanging from the wall'"}),
        ("combustible", {"type": "bool", "tooltip": "defines whether this item "
                         "will burn"}),
        ("energy", {"type": "int", "tooltip": "defines health gained by player "
                            "from eating this item (if edible)"}),
        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                            "from selling this item"})
    ])
