from text_game_maker.player import player
from text_game_maker.tile import tile
from text_game_maker.game_objects import __object_model_version__ as obj_version

VERSION = "1.0.1"
VERSION_KEY = "tgmdata_version"

class VersionMigration(object):
    def __init__(self, from_version, to_version, migration_function):
        self.from_version = from_version
        self.to_version = to_version
        self._do_migration = migration_function

    def migrate(self, attrs):
        return self._do_migration(attrs)

def migrate_noversion_100(attrs):
    # Fix save files created before the 'islands' attribute was added
    attrs['islands'] = []
    return attrs

def migrate_100_101(attrs):
    # Fix save files created before we started setting 'original_name' on new tiles
    for tiledata in attrs[player.TILES_KEY]:
        tiledata["original_name"] = tiledata["name"]

    return attrs

migrations = [
    VersionMigration(None, "1.0.0", migrate_noversion_100),
    VersionMigration("1.0.0", "1.0.1", migrate_100_101)
]

def migrate_tgmdata_version(attrs):
    curr_version = attrs[VERSION_KEY] if VERSION_KEY in attrs else None

    for migration in migrations:
        if migration.from_version == curr_version:
            attrs = migration.migrate(attrs)
            curr_version = migration.to_version

    return attrs

def tile_id_in_map_data(tile_list, tile_id):
    for tiledata in tile_list:
        if tiledata["tile_id"] == tile_id:
            return True

    return False

def serialize(start_tile, tile_dict):
    attrs = {}
    attrs[player.OBJECT_VERSION_KEY] = obj_version
    attrs[player.TILES_KEY] = tile.crawler(start_tile)
    attrs[player.START_TILE_KEY] = start_tile.tile_id
    attrs[VERSION_KEY] = VERSION
    attrs['positions'] = {}
    attrs['islands'] = []

    for pos in tile_dict:
        tileobj = tile_dict[pos]

        # Save tile position
        attrs['positions'][tileobj.tile_id] = list(pos)

        # If this tile wasn't caught by the crawler, then it's part of an island--
        # Run the crawler again with this tile as the start tile
        in_tile_map = tile_id_in_map_data(attrs[player.TILES_KEY], tileobj.tile_id)
        in_islands = False

        for tile_list in attrs['islands']:
            if tile_id_in_map_data(tile_list, tileobj.tile_id):
                in_islands = True
                break

        if (not in_tile_map) and (not in_islands):
            attrs['islands'].append(tile.crawler(tileobj))

    return attrs

def deserialize(attrs):
    attrs = migrate_tgmdata_version(attrs)

    start_tile = tile.builder(attrs[player.TILES_KEY],
                              attrs[player.START_TILE_KEY],
                              attrs[player.OBJECT_VERSION_KEY])

    # Re-build island tiles
    for tile_list in attrs['islands']:
        tiledata = tile_list[0]
        tile.builder(tile_list, tiledata["tile_id"],
                     attrs[player.OBJECT_VERSION_KEY],
                     clear_old_tiles=False)

    return start_tile
