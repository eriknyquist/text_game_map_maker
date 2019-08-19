class AutoFormSettings(object):
    def __init__(self):
        if not hasattr(self, "spec"):
            raise RuntimeError("%s instance has no 'spec' attribute"
                               % self.__class__.__name__)

        for attrname in self.spec.keys():
            setattr(self, attrname, None)

class WallSettings(AutoFormSettings):
    spec = {
        "north": {"type": "bool"},
        "south": {"type": "bool"},
        "east": {"type": "bool"},
        "west": {"type": "bool"}
    }

class DoorSettings(AutoFormSettings):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"}
    }

class KeypadDoorSettings(AutoFormSettings):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"},
        "code": {"type": "int", "label": "keypad code"},
        "prompt": {"type": "str", "label": "keypad prompt"}
    }

class TileSettings(AutoFormSettings):
    spec = {
        'description': {'type':'long_str'},
        'name': {'type': 'str'},
        'tile_id': {'type': 'str', 'label': 'tile ID'},
        'first_visit_message': {'type': 'long_str', 'label': 'first visit message'},
        'first_visit_message_in_dark': {'type': 'bool', 'label': 'show first visit message if dark'},
        'dark': {'type': 'bool'},
        'smell_description': {'type': 'str', 'label': 'smell description'},
        'ground_smell_description': {'type': 'str', 'label': 'ground smell description'},
        'ground_taste_description': {'type': 'str', 'label': 'ground taste description'}
    }
