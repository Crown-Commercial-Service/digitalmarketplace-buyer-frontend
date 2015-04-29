import os
from requests.exceptions import ConnectionError


def get_version_label():
    try:
        path = os.path.join(os.path.dirname(__file__),
                            '..', '..', 'version_label')
        with open(path) as f:
            return f.read().strip()
    except IOError:
        return None


def return_result_of_api_status_call(function_call):

    api_status = "error"

    try:
        api_status_response = function_call()

        if api_status_response.status_code is 200:
            api_status = "ok"

    except ConnectionError:
        pass

    return api_status
