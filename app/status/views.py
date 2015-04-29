from flask import jsonify, current_app

from . import status
from . import utils
from .. import models


@status.route('/_status')
def status():

    data_api_status = utils.return_result_of_api_status_call(
        models.get_data_api_status
    )

    search_api_status = utils.return_result_of_api_status_call(
        models.get_search_api_status
    )

    if data_api_status is "ok" and search_api_status is "ok":

        return jsonify(
            status="ok",
            version=utils.get_version_label(),
            data_api_status=data_api_status,
            search_api_status=search_api_status
            )

    apis_wot_got_errors = []

    if data_api_status is not "ok":
        apis_wot_got_errors.append("Data API")

    if search_api_status is not "ok":
        apis_wot_got_errors.append("Search API")

    # logic breaks down once we hit 3 APIs.
    message = "Error connecting to the " \
              + (" and the ".join(apis_wot_got_errors)) \
              + "."

    current_app.logger.error(message)
    return jsonify(
        status="error",
        app_version=utils.get_version_label(),
        data_api_status=data_api_status,
        search_api_status=search_api_status,
        message=message,
    ), 500
