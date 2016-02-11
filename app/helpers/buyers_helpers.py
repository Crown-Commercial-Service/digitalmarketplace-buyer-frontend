from flask import abort

from app import data_api_client


def get_framework_and_lot(framework_slug, lot_slug):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)

    return framework, lot


def count_suppliers_on_lot(framework, lot):

    # TODO: Implement this properly!

    return 987
