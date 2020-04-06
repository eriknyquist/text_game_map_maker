import copy

from text_game_maker.game_objects.base import serialize, deserialize
from text_game_maker.game_objects import __object_model_version__ as obj_version


_objects = {}


def _obj_name(obj):
    return "(%s) %s %s" % (obj.__class__.__name__, obj.prefix, obj.name)

def save_object(obj):
    """
    Save an object for later re-use
    """
    name = _obj_name(obj)
    if hasattr(obj, 'home'):
        obj.home = None

    _objects[name] = copy.deepcopy(obj)

def get_object_names():
    """
    Returns a list of names for all saved objects
    """
    return list(_objects.keys())

def get_objects():
    """
    Returns all serialized object data
    """
    return _objects

def set_objects(objs):
    """
    Replace saved objects with serialized objects from save file
    """
    _objects.clear()
    for name in objs:
        attrs = objs[name]
        _objects[name] = deserialize(attrs, obj_version)

def get_object_by_name(name):
    """
    Access a saved object by name; create a new instance and return it.
    """
    if name not in _objects:
        return None

    return copy.deepcopy(_objects[name])

def clear_objects():
    """
    Clear all saved objects
    """
    _objects = {}

def delete_object(obj):
    """
    Delete a saved object
    """
    name = _obj_name(obj)
    if name in _objects:
        del _objects[name]

def delete_object_by_name(name):
    """
    Delete a saved object by name
    """
    if name in _objects:
        del _objects[name]
