from collections import OrderedDict

from PyQt5 import QtWidgets, QtCore, QtGui

from text_game_map_maker.constants import available_item_sizes

from text_game_maker.materials import materials

from text_game_maker.game_objects.items import (
    Item, Food, ItemSize, Flashlight, Battery, Coins, PaperBag, SmallBag, Bag,
    LargeBag, SmallTin, Lighter, BoxOfMatches, Lockpick, StrongLockpick, Container,
    LargeContainer, Furniture, Blueprint
)

class ObjectBuilder(object):
    objtype = None
    spec = None

    def __init__(self):
        self.title = "%s editor" % self.__class__.objtype.__name__
        self.formTitle = ""
        self.desc = ""

        if self.__class__.objtype.__doc__:
            self.desc = ''.join(self.__class__.objtype.__doc__.strip().split('\n'))

    def build_instance(self, formclass):
        ins = self.__class__.objtype()
        dialog = formclass(ins, title=self.title, formTitle=self.formTitle,
                           headerText=self.desc, scrollable=True, spec=self.__class__.spec)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        if not dialog.wasAccepted():
            return None

        self.process_dialog_settings(ins)
        return ins

    def edit_instance(self, ins, formclass):
        dialog = formclass(ins, title=self.title, formTitle=self.formTitle,
                           headerText=self.desc, scrollable=True, spec=self.__class__.spec)
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
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

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
                                             "from selling this item"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."}),

        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"})
    ])


class FurnitureBuilder(ObjectBuilder):
    objtype = Furniture
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("combustible", {"type": "bool", "tooltip": "defines whether this item "
                                                    "will burn"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."}),

        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"})
    ])


class ContainerBuilder(ObjectBuilder):
    objtype = Container
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("combustible", {"type": "bool", "tooltip": "defines whether this item "
                                                    "will burn"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."}),

        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"})
    ])


class BlueprintBuilder(ObjectBuilder):
    objtype = Blueprint
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),
    ])


class LargeContainerBuilder(ObjectBuilder):
    objtype = LargeContainer
    spec = ContainerBuilder.spec


class FlashlightBuilder(ObjectBuilder):
    objtype = Flashlight
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("damage", {"type": "int", "tooltip": "defines health lost by player "
                                              "if damaged by this item"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("fuel_decrement", {"type": "float", "label": "fuel decrement",
                      "tooltip": "defines how much fuel is lost per item use"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."})
    ])


class BatteryBuilder(ObjectBuilder):
    objtype = Battery
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("fuel", {"type": "float", "tooltip": "current fuel level"})
    ])


class LighterBuilder(ObjectBuilder):
    objtype = Lighter
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("max_fuel", {"type": "float", "label": "Max. fuel",
                      "tooltip": "defines maximum possible fuel level value"}),

        ("fuel_decrement", {"type": "float", "label": "fuel decrement",
                      "tooltip": "defines how much fuel is lost per item use"}),

        ("fuel", {"type": "float", "tooltip": "current fuel level"})
    ])


class BoxOfMatchesBuilder(ObjectBuilder):
    objtype = BoxOfMatches
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("max_fuel", {"type": "float", "label": "Max. fuel",
                      "tooltip": "defines maximum possible fuel level value"}),

        ("fuel_decrement", {"type": "float", "label": "fuel decrement",
                      "tooltip": "defines how much fuel is lost per item use"}),

        ("fuel", {"type": "float", "tooltip": "current fuel level"})
    ])


class LockpickBuilder(ObjectBuilder):
    objtype = Lockpick
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("uses", {"type": "int", "tooltip": "number of times lockpick can be "
                                            "used before breaking"})
    ])


class StrongLockpickBuilder(ObjectBuilder):
    objtype = StrongLockpick
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                                              "the name of this object, usually 'a' "
                                              "or 'an' (e.g. 'a' sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                                            "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("uses", {"type": "int", "tooltip": "number of times lockpick can be "
                                            "used before breaking"})
    ])


class CoinsBuilder(ObjectBuilder):
    objtype = Coins
    spec = OrderedDict([
        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),
    ])


class PaperBagBuilder(ObjectBuilder):
    objtype = PaperBag
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),
    ])


class SmallBagBuilder(ObjectBuilder):
    objtype = SmallBag
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("capacity", {"type": "int", "tooltip": "defines number of items this bag "
                                                "can hold"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."})
    ])


class SmallTinBuilder(ObjectBuilder):
    objtype = SmallTin
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("capacity", {"type": "int", "tooltip": "defines number of items this bag "
                                                "can hold"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."})
    ])


class BagBuilder(ObjectBuilder):
    objtype = Bag
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("capacity", {"type": "int", "tooltip": "defines number of items this bag "
                                                "can hold"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."})
    ])


class LargeBagBuilder(ObjectBuilder):
    objtype = LargeBag
    spec = OrderedDict([
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                    "the name of this object, usually 'a' or 'an' (e.g. 'a' "
                    "sandwich, 'an' apple)"}),

        ("name", {"type": "str", "tooltip": "name of this object, e.g. "
                  "'sandwich' or 'apple'"}),

        ("location", {"type": "str", "tooltip": "location of object, e.g. "
                                                "'on the floor' or 'hanging from the wall'"}),

        ("value", {"type": "int", "tooltip": "defines coins gained by player "
                                             "from selling this item"}),

        ("capacity", {"type": "int", "tooltip": "defines number of items this bag "
                                                "can hold"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."})
    ])


class FoodBuilder(ObjectBuilder):
    objtype = Food
    spec = OrderedDict([
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
                            "from selling this item"}),

        ("size", {"type": "choice", "choices": available_item_sizes,
                  "tooltip": "defines size class for this item. "
                             "items cannot contain items of a larger size class."}),

        ("material", {"type": "choice", "choices": materials.get_materials(),
                      "tooltip": "Set this object's material type"})
    ])


