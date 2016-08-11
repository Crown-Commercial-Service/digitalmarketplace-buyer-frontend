from flask import jsonify, current_app, request

from . import status
from .. import data_api_client
from dmutils.status import get_flags


@status.route('/_status')
def status():

    if 'ignore-dependencies' in request.args:
        return jsonify(
            status="ok",
        ), 200

    version = current_app.config['VERSION']
    apis = [
        {
            'name': '(Data) API',
            'key': 'api_status',
            'status': data_api_client.get_status()
        },
    ]

    apis_with_errors = []

    for api in apis:
        if api['status'] is None or api['status']['status'] != "ok":
            apis_with_errors.append(api['name'])

    stats = {api['key']: api['status'] for api in apis}
    stats.update({
        'version': version,
        'flags': get_flags(current_app)
    })

    if apis_with_errors:
        stats['status'] = 'error'
        stats['message'] = 'Error connecting to the {}.'.format(
            ' and the '.join(apis_with_errors)
        )
        return jsonify(**stats), 500

    stats['status'] = 'ok'
    return jsonify(**stats), 200
