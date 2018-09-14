import os

from flask import Flask, request
from flask_cache import Cache
from flask_login import LoginManager

import dmapiclient
from dmutils import init_app, init_frontend_app
from dmutils.user import User
from dmcontent.content_loader import ContentLoader

from config import configs
from app.helpers.terms_helpers import TermsManager

from react.render import render_component

cache = Cache()
login_manager = LoginManager()
data_api_client = dmapiclient.DataAPIClient()

content_loader = ContentLoader('app/content')
content_loader.load_manifest('g-cloud-6', 'services', 'search_filters')
content_loader.load_manifest('g-cloud-6', 'services', 'display_service')
content_loader.load_manifest('digital-outcomes-and-specialists', 'briefs', 'display_brief')
content_loader.load_manifest('digital-service-professionals', 'briefs', 'display_brief')
content_loader.load_manifest('digital-marketplace', 'briefs', 'display_brief')


def create_app(config_name):
    asset_path = os.environ.get('ASSET_PATH', configs[config_name].ASSET_PATH)
    application = Flask(__name__, static_url_path=asset_path)

    init_app(
        application,
        configs[config_name],
        data_api_client=data_api_client,
        login_manager=login_manager,
        cache=cache,
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

    init_frontend_app(application, data_api_client, login_manager)

    @login_manager.user_loader
    def load_user(user_id):
        if request.path.startswith(asset_path):
            return
        return User.load_user(data_api_client, user_id)

    terms_manager = TermsManager()
    terms_manager.init_app(application)

    def component_filter(x, thing, *args, **kwargs):
        from jinja2 import Markup  # , escape
        from flask import current_app

        COMPONENTS = 'components'
        EXTENSION = '.html'

        t = current_app.jinja_env.get_template(
            COMPONENTS + '/' + thing + EXTENSION)
        return Markup(t.render(x=x, **kwargs))

    application.jinja_env.filters['as'] = component_filter
    application.jinja_env.globals.update(render_component=render_component)

    return application
