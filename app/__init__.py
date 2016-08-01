from flask import Flask, request, redirect, session, abort
from flask_login import LoginManager, current_user

import dmapiclient
from dmutils import init_app, flask_featureflags
from dmcontent.content_loader import ContentLoader
from dmutils.user import User

from config import configs

login_manager = LoginManager()
data_api_client = dmapiclient.DataAPIClient()
search_api_client = dmapiclient.SearchAPIClient()
feature_flags = flask_featureflags.FeatureFlag()

content_loader = ContentLoader('app/content')
content_loader.load_manifest('g-cloud-6', 'services', 'search_filters')
content_loader.load_manifest('g-cloud-6', 'services', 'display_service')
content_loader.load_manifest('digital-outcomes-and-specialists', 'briefs', 'display_brief')


def create_app(config_name):
    application = Flask(__name__, static_url_path=configs[config_name].ASSET_PATH)

    init_app(
        application,
        configs[config_name],
        data_api_client=data_api_client,
        feature_flags=feature_flags,
        login_manager=login_manager,
        search_api_client=search_api_client
    )

    from .main import main as main_blueprint
    from .status import status as status_blueprint
    from .buyers import buyers as buyers_blueprint

    url_prefix = application.config['URL_PREFIX']
    application.register_blueprint(status_blueprint, url_prefix=url_prefix)
    application.register_blueprint(main_blueprint, url_prefix=url_prefix)
    application.register_blueprint(buyers_blueprint, url_prefix=url_prefix)

    login_manager.login_view = 'main.render_login'
    login_manager.login_message_category = "must_login"

    @application.before_request
    def set_scheme():
        request.environ['wsgi.url_scheme'] = application.config['DM_HTTP_PROTO']

    @application.before_request
    def remove_trailing_slash():
        if request.path != application.config['URL_PREFIX'] + '/' and request.path.endswith('/'):
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

    @application.after_request
    def add_cache_control(response):
        if request.method != 'GET' or response.status_code in (301, 302):
            return response
        if current_user.is_authenticated:
            response.cache_control.private = True
        if response.cache_control.max_age is None:
            response.cache_control.max_age = application.config['DM_DEFAULT_CACHE_MAX_AGE']
        return response

    return application


@login_manager.user_loader
def load_user(user_id):
    return User.load_user(data_api_client, user_id)
