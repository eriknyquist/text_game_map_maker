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
    attrs = serialize(obj)
    _objects[name] = attrs

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
    _objects.update(objs)

def get_object_by_name(name):
    """
    Access a saved object by name; create a new instance and return it.
    """
    if name not in _objects:
        return None

    attrs = _objects[name]
    return deserialize(attrs, obj_version)

def clear_objects():
    """
    Clear all saved objects
    """
    _objects = {}

def delete_object_by_name(name):
    """
    Delete a saved object by name
    """
    if name in _objects:
        del _objects[name]
