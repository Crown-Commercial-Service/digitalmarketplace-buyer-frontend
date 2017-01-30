from flask import Blueprint, current_app, flash
from flask_login import current_user, login_required
from dmcontent.content_loader import ContentLoader

buyers = Blueprint('buyers', __name__)
dos = Blueprint('dos', __name__)

content_loader = ContentLoader('app/content')
content_loader.load_manifest('digital-outcomes-and-specialists', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'output_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'legacy_output_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'clarification_question', 'clarification_question')


content_loader.load_manifest('digital-outcomes-and-specialists-2', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'brief-responses', 'output_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'clarification_question', 'clarification_question')


@buyers.before_request
@login_required
def require_login():
    if current_user.is_authenticated() and current_user.role != 'buyer':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()


@buyers.after_request
def add_cache_control(response):
    response.cache_control.no_cache = True
    return response

from ..main import errors
from .views import buyers as buyers_views
from .views import digital_outcomes_and_specialists
