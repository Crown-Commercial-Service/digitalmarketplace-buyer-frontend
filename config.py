import os
import jinja2

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    BASE_TEMPLATE_DATA = {
        'asset_path': '/static/',
        'header_class': 'with-proposition'
    }
    DM_DATA_API_URL = os.getenv('DM_API_URL')
    DM_DATA_API_AUTH_TOKEN = os.getenv('DM_BUYER_FRONTEND_API_AUTH_TOKEN')
    DM_SEARCH_API_URL = os.getenv('DM_SEARCH_API_URL')
    DM_SEARCH_API_AUTH_TOKEN = os.getenv(
        'DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN'
    )
    # This is just a placeholder
    ES_ENABLED = True

    # Search API
    DM_SEARCH_API_URL = "http://localhost:5001"
    DM_SEARCH_API_AUTH_TOKEN = "myToken"
    ES_ENABLED = True

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"

    # LOGGING
    DM_LOG_LEVEL = 'DEBUG'
    DM_APP_NAME = 'buyer-frontend'
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Amz-Cf-Id'

    @staticmethod
    def init_app(app):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        template_folders = [
            os.path.join(repo_root, 'app/templates'),
            os.path.join(
                repo_root, 'bower_components/govuk_template/views/layouts'
            )
        ]
        jinja_loader = jinja2.FileSystemLoader(template_folders)
        app.jinja_loader = jinja_loader


class Development(Config):
    DEBUG = True


class Live(Config):
    DEBUG = False


configs = {
    'development': Development,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Development,
}
