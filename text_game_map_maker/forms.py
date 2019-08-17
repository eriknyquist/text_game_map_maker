class DoorSettings(object):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"}
    }

    def __init__(self):
        self.prefix = ""
        self.name = ""
        self.direction = ""
        self.tile_id = ""

class KeypadDoorSettings(object):
    spec = {
        "direction": {"type": "choice", "choices": ["north", "south", "east", "west"]},
        "prefix": {"type": "str"},
        "name": {"type": "str"},
        "tile_id": {"type": "str", "label": "tile ID"},
        "code": {"type": "int", "label": "keypad code"},
        "prompt": {"type": "str", "label": "keypad prompt"}
    }

    def __init__(self):
        self.prefix = ""
        self.name = ""
        self.direction = ""
        self.tile_id = ""
        self.code = 0
        self.prompt = ""

class TileSettings(object):
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

    def __init__(self):
        self.description = ""
        self.name = ""
        self.tile_id = ""
        self.first_visit_message = ""
        self.first_visit_message_in_dark = True
        self.dark = False
        self.smell_description = ""
        self.ground_smell_description = ""
        self.ground_taste_description = ""

