from flask import Blueprint

main = Blueprint('main', __name__)

from . import errors
from .views import (
    crown_hosting, g_cloud, login, marketplace, suppliers,
    digital_outcomes_and_specialists
)
