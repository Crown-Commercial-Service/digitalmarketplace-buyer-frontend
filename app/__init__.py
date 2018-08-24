from flask import Flask, request, redirect, session, abort
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError

import dmapiclient
from dmutils import init_app
from dmcontent.content_loader import ContentLoader
from dmcontent.utils import try_load_manifest, try_load_metadata, try_load_messages
from dmutils.user import User
from dmutils.external import external as external_blueprint

from config import configs


login_manager = LoginManager()
data_api_client = dmapiclient.DataAPIClient()
search_api_client = dmapiclient.SearchAPIClient()
csrf = CSRFProtect()

content_loader = ContentLoader('app/content')
from .main.helpers.framework_helpers import get_latest_live_framework
from .main.helpers.search_save_helpers import SavedSearchStateEnum


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        data_api_client=data_api_client,
        login_manager=login_manager,
        search_api_client=search_api_client,
    )

    frameworks = data_api_client.find_frameworks().get('frameworks')
    for framework_data in frameworks:
        if not framework_data['slug'] in application.config.get('DM_FRAMEWORK_CONTENT_MAP', {}):
            if framework_data['framework'] == 'g-cloud':
                content_loader.load_manifest(framework_data['slug'], 'services', 'services_search_filters')
                # we need to be able to display old services, even on expired frameworks
                content_loader.load_manifest(framework_data['slug'], 'services', 'display_service')
                content_loader.load_manifest(framework_data['slug'], 'services', 'download_results')
                try_load_metadata(content_loader, application, framework_data, ['following_framework'])
            elif framework_data['framework'] == 'digital-outcomes-and-specialists':
                content_loader.load_manifest(framework_data['slug'], 'briefs', 'display_brief')
                try_load_manifest(content_loader, application, framework_data, 'briefs', 'briefs_search_filters')

    from .main import main as main_blueprint
    from .main import direct_award as direct_award_blueprint
    from .main import direct_award_public as direct_award_public_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)
    application.register_blueprint(direct_award_blueprint)
    # direct_award_blueprint and direct_award_public_blueprint cover the same url prefix - direct_award_blueprint takes
    # precedence
    application.register_blueprint(direct_award_public_blueprint)

    # Must be registered last so that any routes declared in the app are registered first (i.e. take precedence over
    # the external NotImplemented routes in the dm-utils external blueprint).
    application.register_blueprint(external_blueprint)

    login_manager.login_view = '/user/login'
    login_manager.login_message_category = "must_login"
    csrf.init_app(application)

    @application.before_request
    def remove_trailing_slash():
        if request.path != '/' and request.path.endswith('/'):
            if request.query_string:
                return redirect(
                    '{}?{}'.format(
                        request.path[:-1],
                        request.query_string.decode('utf-8')
                    ),
                    code=301
                )
            else:
                return redirect(request.path[:-1], code=301)

    @application.before_request
    def refresh_session():
        session.permanent = True
        session.modified = True

    @application.context_processor
    def inject_saved_search_temp_message_statuses():
        return {state.name: state.value for state in SavedSearchStateEnum}

    return application


@login_manager.user_loader
def load_user(user_id):
    return User.load_user(data_api_client, user_id)
