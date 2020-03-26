from collections import OrderedDict


class AutoFormSettings(object):
    def __init__(self):
        if not hasattr(self, "spec"):
            raise RuntimeError("%s instance has no 'spec' attribute"
                               % self.__class__.__name__)

        for attrname in self.spec.keys():
            setattr(self, attrname, None)

class WallSettings(AutoFormSettings):
    spec = OrderedDict([
        ("north", {"type": "bool", "tooltip": "Enable/disable wall to the north"}),
        ("south", {"type": "bool", "tooltip": "Enable/disable wall to the south"}),
        ("east", {"type": "bool", "tooltip": "Enable/disable wall to the east"}),
        ("west", {"type": "bool", "tooltip": "Enable/disable wall to the west"})
    ])

class DoorSettings(AutoFormSettings):
    spec = OrderedDict([
        ("direction", {"type": "choice", "choices": ["north", "south", "east", "west"],
                      "tooltip": "Set the direction to this door from currently"
                      " selected tile"}),
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                   "the name of this door, usually 'a' or 'an' (e.g. 'a' "
                   "wooden door, 'an' oak door)"}),
        ("name", {"type": "str", "tooltip": "name of this door, e.g. "
                 "'wooden door' or 'oak door'"}),
        ("tile_id", {"type": "str", "label": "tile ID", "tooltip": "unique "
                    "identifier for programmatic access to this door"})
    ])

class KeypadDoorSettings(AutoFormSettings):
    spec = OrderedDict([
        ("direction", {"type": "choice", "choices": ["north", "south", "east", "west"],
                      "tooltip": "Set the direction to this door from currently"
                      " selected tile"}),
        ("prefix", {"type": "str", "tooltip": "Set the word that should precede "
                   "the name of this door, usually 'a' or 'an' (e.g. 'a' "
                   "wooden door, 'an' oak door)"}),
        ("name", {"type": "str", "tooltip": "name of this door, e.g. "
                 "'wooden door' or 'oak door'"}),
        ("tile_id", {"type": "str", "label": "tile ID", "tooltip": "unique "
                    "identifier for programmatic access to this door"}),
        ("code", {"type": "int", "label": "keypad code", "tooltip": "Integer "
                 "code required to unlock this door"}),
        ("prompt", {"type": "str", "label": "keypad prompt", "tooltip": "String "
                   "used to prompt player for keypad code entry"})
    ])

class TileSettings(AutoFormSettings):
    spec = OrderedDict([
        ('tile_id', {'type': 'str', 'label': 'tile ID', "tooltip": "Unique "
                    "identifier for programmatic access to this tile"}),
        ('name', {'type': 'str', 'tooltip': "Short string used to describe this "
                 "tile to the player from afar, e.g. 'a scary room'"}),
        ('description', {'type':'long_str', 'tooltip': "String used to describe "
                        "the tile to player when they enter it. Note that this "
                        "string will always be prefixed with 'You are' during "
                        "gameplay"}),
        ('dark', {'type': 'bool', 'tooltip': "If enabled, player will need a "
                 "light source to see anything on this tile"}),
        ('first_visit_message', {'type': 'long_str', 'label': 'first visit message',
                                'tooltip': "String displayed only when player "
                                "enters this tile for the first time"}),
        ('first_visit_message_in_dark', {'type': 'bool', 'label': 'show first visit message if dark',
                                        'tooltip': "Enable/disable showing the "
                                        "first visit message if the current tile "
                                        "is dark"}),
        ('smell_description', {'type': 'str', 'label': 'smell description',
                              'tooltip': "String displayed when player smells "
                              "the air on the current tile"}),
        ('ground_smell_description', {'type': 'str', 'label': 'ground smell description',
                                     'tooltip': "String displayed when player "
                                     "smells the ground on the current tile"}),
        ('ground_taste_description', {'type': 'str', 'label': 'ground taste description',
                                     'tooltip': "String displayed when player "
                                     "tastes the ground on the current tile"}),
        ('name_from_north', {'type': 'str', 'label': 'name from south',
                             'tooltip': 'String used to describe this tile when'
                             ' player is on the adjacent tile to the south'}),
        ('name_from_south', {'type': 'str', 'label': 'name from south',
                             'tooltip': 'String used to describe this tile when'
                             ' player is on the adjacent tile to the south'}),
        ('name_from_east', {'type': 'str', 'label': 'name from east',
                            'tooltip': 'String used to describe this tile when'
                            ' player is on the adjacent tile to the east'}),
        ('name_from_west', {'type': 'str', 'label': 'name from west',
                            'tooltip': 'String used to describe this tile when'
                            ' player is on the adjacent tile to the west'})
    ])
