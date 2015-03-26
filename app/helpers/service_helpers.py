def get_lot_name_from_acronym(blueprint, acronym):
    """Return the full lot name for its acronym"""

    return blueprint.config['LOTS'][acronym]
