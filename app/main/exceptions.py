from flask import current_app


class AuthBaseException(ValueError):
    """Base class for authentication exceptions."""
    pass


class AuthException(AuthBaseException):
    """Auth process exception."""
    def __init__(self, backend, *args, **kwargs):
        self.backend = backend
        super(AuthException, self).__init__(*args, **kwargs)
        current_app.logger.error('An authentication error occurred')
