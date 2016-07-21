REQUEST_ERROR_STATUS_CODE = 503
REQUEST_ERROR_MESSAGE = "Request failed"


class APIError(Exception):
    def __init__(self, response=None, message=None):
        self.response = response
        self._message = message

    @property
    def message(self):
        try:
            return self.response.json()['error']
        except (TypeError, ValueError, AttributeError, KeyError):
            return self._message or REQUEST_ERROR_MESSAGE

    @property
    def status_code(self):
        try:
            return self.response.status_code
        except AttributeError:
            return REQUEST_ERROR_STATUS_CODE

    def __str__(self):
        return "{} (status: {})".format(self.message, self.status_code)


class HTTPError(APIError):
    @staticmethod
    def create(e):
        error = HTTPError(e.response)
        if error.status_code in [503, 504]:
            error = HTTPTemporaryError(e.response)
        return error


class HTTPTemporaryError(HTTPError):
    """Specific instance of HTTPError for temporary 503 and 504 errors

    Used for detecting whether failed requests should be retried.
    """
    pass


class InvalidResponse(APIError):
    pass
