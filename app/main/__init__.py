from flask import Blueprint, flash, Markup, current_app
from flask_login import login_required, current_user
import flask_featureflags

main = Blueprint('main', __name__)
direct_award = Blueprint('direct_award', __name__, url_prefix='/buyers/direct-award')

LOGIN_REQUIRED_MESSAGE = Markup("""You must log in with a buyer account to see this page.""")


@direct_award.before_request
@flask_featureflags.is_active_feature('DIRECT_AWARD_PROJECTS')
@login_required
def require_login():
    if current_user.is_authenticated() and current_user.role != 'buyer':
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
