def get_lot_name_from_acronym(blueprint, acronym):
    """Return the full lot name for its acronym"""

    if 'aa' in acronym:
        # Capitalize first and last character
        acronym = "{0}{1}{2}".format(
            acronym[:1].upper(), acronym[1:-1], acronym[-1].upper())
    else:
        acronym = acronym.upper()

    try:
        lot = blueprint.config['LOTS'][acronym]
    except KeyError:
        lot = 'Search Results'

    return lot
