from flask import Blueprint

main = Blueprint('main', __name__)
external = Blueprint('external', __name__)

from . import errors
from .views import (
    crown_hosting, digital_services_framework, g_cloud,
    login, marketplace, suppliers
)

from .views import external as external_views
