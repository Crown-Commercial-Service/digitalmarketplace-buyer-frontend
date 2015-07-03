import os
import jinja2
from dmutils.status import enabled_since, get_version_label

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
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
    # matches api(s)
    DM_SEARCH_PAGE_SIZE = 100

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

    # Feature Flags
    RAISE_ERROR_ON_MISSING_FEATURES = True

    @staticmethod
    def init_app(app):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        template_folders = [
            os.path.join(repo_root, 'app/templates')
        ]
        jinja_loader = jinja2.FileSystemLoader(template_folders)
        app.jinja_loader = jinja_loader


class Test(Config):
    DEBUG = True
    DM_LOG_LEVEL = 'CRITICAL'


class Development(Config):
    DEBUG = True

    DM_SEARCH_PAGE_SIZE = 5


class Live(Config):
    DEBUG = False


configs = {
    'development': Development,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Test,
}
