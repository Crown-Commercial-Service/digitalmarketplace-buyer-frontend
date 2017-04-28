from flask import jsonify, current_app, request

from . import status
from .. import data_api_client, search_api_client
from dmutils.status import get_flags


@status.route('/_status')
def status():
    if 'ignore-dependencies' in request.args:
        return jsonify(
            status="ok",
        ), 200

    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        remote_addr = request.remote_addr or 'untrackable'

    current_app.logger.info(
        "_status.check: buyer app status page requested by {ip_address}",
        extra={'ip_address': remote_addr}
    )

    version = current_app.config['VERSION']
    apis = [
        {
            'name': '(Data) API',
            'key': 'api_status',
            'status': data_api_client.get_status()
        }, {
            'name': 'Search API',
            'key': 'search_api_status',
            'status': search_api_client.get_status()
        }
    ]

    apis_with_errors = []

    for api in apis:
        if api['status'] is None or api['status']['status'] != "ok":
            apis_with_errors.append(api['name'])

    # if no errors found, return as is.  Else, return an error and a message
    if not apis_with_errors:
        return jsonify(
            {api['key']: api['status'] for api in apis},
            status="ok",
            version=version,
            flags=get_flags(current_app),
            remote_address=remote_addr
        )

    message = "Error connecting to the {}.".format(
        " and the ".join(apis_with_errors)
    )

    return jsonify(
        {api['key']: api['status'] for api in apis},
        status="error",
        version=version,
        message=message,
        flags=get_flags(current_app),
        remote_address=remote_addr
    ), 500
