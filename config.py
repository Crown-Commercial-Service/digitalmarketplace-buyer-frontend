import os
import hashlib
import jinja2
from dmutils.status import enabled_since, get_version_label
from dmutils.asset_fingerprint import AssetFingerprinter

basedir = os.path.abspath(os.path.dirname(__file__))


def get_asset_fingerprint(asset_file_path):
    hasher = hashlib.md5()
    with open(asset_file_path, 'rb') as asset_file:
        buf = asset_file.read()
        hasher.update(buf)
    return hasher.hexdigest()


class Config(object):

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    URL_PREFIX = '/marketplace'
    SESSION_COOKIE_NAME = 'dm_session'
    SESSION_COOKIE_PATH = '/marketplace/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

    PERMANENT_SESSION_LIFETIME = 4*3600

    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 8*3600
    CSRF_TRUSTED_ORIGINS = 'localhost:5002;dm-dev.apps.staging.digital.gov.au;dm-buyer-frontend.apps.platform.digital.gov.au;www.gov.au;'  # noqa

    DM_DATA_API_URL = None
    DM_DATA_API_AUTH_TOKEN = None
    DM_SEARCH_API_URL = None
    DM_SEARCH_API_AUTH_TOKEN = None
    DM_MANDRILL_API_KEY = None

    # matches api(s)
    DM_SEARCH_PAGE_SIZE = 100

    # This is just a placeholder
    ES_ENABLED = True

    DEBUG = False

    RESET_PASSWORD_EMAIL_NAME = 'Digital Marketplace Admin'
    RESET_PASSWORD_EMAIL_FROM = 'enquiries@digitalmarketplace.service.gov.uk'
    RESET_PASSWORD_EMAIL_SUBJECT = 'Reset your Digital Marketplace password'

    CREATE_USER_SUBJECT = 'Create your Digital Marketplace account'
    SECRET_KEY = None
    SHARED_EMAIL_KEY = None
    RESET_PASSWORD_SALT = 'ResetPasswordSalt'
    INVITE_EMAIL_SALT = 'InviteEmailSalt'

    ASSET_PATH = URL_PREFIX + '/static'
    BASE_TEMPLATE_DATA = {
        'header_class': 'with-proposition',
        'asset_path': ASSET_PATH + '/',
        'asset_fingerprinter': AssetFingerprinter(asset_root=ASSET_PATH + '/')
    }

    # Feature Flags
    RAISE_ERROR_ON_MISSING_FEATURES = True

    # LOGGING
    DM_LOG_LEVEL = 'DEBUG'
    DM_LOG_PATH = None
    DM_APP_NAME = 'buyer-frontend'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Amz-Cf-Id'

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
    CSRF_ENABLED = False

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_SEARCH_API_URL = "http://localhost:5001"
    DM_SEARCH_API_AUTH_TOKEN = "myToken"

    DM_MANDRILL_API_KEY = 'MANDRILL'
    SHARED_EMAIL_KEY = "KEY"
    SECRET_KEY = "KEY"


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    DM_SEARCH_PAGE_SIZE = 5

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_SEARCH_API_URL = "http://localhost:5001"
    DM_SEARCH_API_AUTH_TOKEN = "myToken"

    DM_MANDRILL_API_KEY = "not_a_real_key"
    SECRET_KEY = "verySecretKey"
    SHARED_EMAIL_KEY = "very_secret"


class Live(Config):
    """Base config for deployed environments"""
    DEBUG = False
    DM_HTTP_PROTO = 'https'


class Preview(Live):
    pass


class Staging(Live):
    pass


class Production(Live):
    pass


configs = {
    'development': Development,
    'test': Test,

    'preview': Preview,
    'staging': Staging,
    'production': Production,
}
