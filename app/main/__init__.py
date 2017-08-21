from flask import Blueprint

main = Blueprint('main', __name__)

from . import errors  # noqa
from .views import (  # noqa
    login, marketplace, suppliers, search
)
