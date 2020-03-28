from text_game_maker.game_objects.items import ItemSize

available_item_sizes = [k for k in ItemSize.__dict__ if not k.startswith('_')]
