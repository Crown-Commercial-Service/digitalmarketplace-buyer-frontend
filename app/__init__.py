from flask import Flask, request, redirect, session, abort
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError

import dmapiclient
from dmutils import init_app, flask_featureflags
from dmcontent.content_loader import ContentLoader
from dmutils.user import User
from dmutils.external import external as external_blueprint

from config import configs


login_manager = LoginManager()
data_api_client = dmapiclient.DataAPIClient()
search_api_client = dmapiclient.SearchAPIClient()
feature_flags = flask_featureflags.FeatureFlag()
csrf = CSRFProtect()

content_loader = ContentLoader('app/content')
from .main.helpers.framework_helpers import get_latest_live_framework


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        data_api_client=data_api_client,
        feature_flags=feature_flags,
        login_manager=login_manager,
        search_api_client=search_api_client
    )

    frameworks = data_api_client.find_frameworks().get('frameworks')
    for framework_data in frameworks:
        if not framework_data['slug'] in application.config.get('DM_FRAMEWORK_CONTENT_MAP', {}):
            if framework_data['framework'] == 'g-cloud':
                content_loader.load_manifest(framework_data['slug'], 'services', 'services_search_filters')
                # we need to be able to display old services, even on expired frameworks
                content_loader.load_manifest(framework_data['slug'], 'services', 'display_service')
                content_loader.load_manifest(framework_data['slug'], 'services', 'download_results')
            elif framework_data['framework'] == 'digital-outcomes-and-specialists':
                content_loader.load_manifest(framework_data['slug'], 'briefs', 'display_brief')

    content_loader.load_manifest(
        get_latest_live_framework(frameworks, 'digital-outcomes-and-specialists')['slug'],
        'briefs',
        'briefs_search_filters',
    )

    from .main import main as main_blueprint
    from .main import direct_award as direct_award_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)
    application.register_blueprint(direct_award_blueprint)

    # Must be registered last so that any routes declared in the app are registered first (i.e. take precedence over
    # the external NotImplemented routes in the dm-utils external blueprint).
    application.register_blueprint(external_blueprint)

    login_manager.login_view = '/user/login'
    login_manager.login_message_category = "must_login"
    csrf.init_app(application)

    @application.errorhandler(CSRFError)
    def csrf_handler(reason):
        if 'user_id' not in session:
            application.logger.info(
                u'csrf.session_expired: Redirecting user to log in page'
            )

            return application.login_manager.unauthorized()

        application.logger.info(
            u'csrf.invalid_token: Aborting request, user_id: {user_id}',
            extra={'user_id': session['user_id']})

        abort(400, reason)

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

    return application


@login_manager.user_loader
def load_user(user_id):
    return User.load_user(data_api_client, user_id)
