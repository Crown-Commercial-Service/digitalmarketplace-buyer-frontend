from flask import Blueprint

main = Blueprint('main', __name__)

from . import errors  # noqa
from .views import (  # noqa
    digital_services_framework, g_cloud, login, marketplace, suppliers,
    digital_outcomes_and_specialists, search, guidance
)
