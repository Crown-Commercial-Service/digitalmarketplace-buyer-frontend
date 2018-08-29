from flask import Blueprint, flash, Markup, current_app
from flask_login import login_required, current_user

main = Blueprint('main', __name__)
direct_award = Blueprint('direct_award', __name__, url_prefix='/buyers/direct-award')
direct_award_public = Blueprint('direct_award_public', __name__, url_prefix='/buyers/direct-award')

LOGIN_REQUIRED_MESSAGE = "You must log in with a buyer account to see this page."


@direct_award.before_request
@login_required
def require_login():
    if current_user.is_authenticated and current_user.role != 'buyer':
        flash(LOGIN_REQUIRED_MESSAGE, 'error')
        return current_app.login_manager.unauthorized()


from . import errors
from .views import (
    crown_hosting,
    digital_services_framework,
    feedback,
    g_cloud,
    marketplace,
    suppliers,
)
