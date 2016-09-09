import os
import hashlib
import jinja2
from dmutils.status import enabled_since, get_version_label

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    URL_PREFIX = ''
    SESSION_COOKIE_NAME = 'dm_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

    PERMANENT_SESSION_LIFETIME = 4*3600

    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 8*3600

    DM_DATA_API_URL = None
    DM_DATA_API_AUTH_TOKEN = None
    DM_HTTP_PROTO = 'http'
    DM_DEFAULT_CACHE_MAX_AGE = 24*3600
    DM_SEND_EMAIL_TO_STDERR = False
    DM_CACHE_TYPE = 'dev'

    DM_CURRENT_TERMS_DATE = '2016-09-02 11:00'

    # matches api(s)
    DM_SEARCH_PAGE_SIZE = 100

    DM_GA_CODE = 'UA-72722909-6'

    # This is just a placeholder
    ES_ENABLED = True

    DEBUG = False

    DM_GENERIC_NOREPLY_EMAIL = 'no-reply@marketplace.digital.gov.au'
    DM_GENERIC_ADMIN_NAME = 'Digital Marketplace Admin'

    DM_GENERIC_SUPPORT_EMAIL = 'marketplace@digital.gov.au'
    DM_GENERIC_SUPPORT_NAME = 'Digital Marketplace'

    RESET_PASSWORD_EMAIL_NAME = DM_GENERIC_ADMIN_NAME
    RESET_PASSWORD_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL
    RESET_PASSWORD_EMAIL_SUBJECT = 'Reset your Digital Marketplace password'

    BUYER_INVITE_REQUEST_SUBJECT = 'Buyer Account Invite Request'
    BUYER_INVITE_REQUEST_ADMIN_EMAIL = 'marketplace+buyer-request@digital.gov.au'
    BUYER_INVITE_REQUEST_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL
    BUYER_INVITE_REQUEST_EMAIL_NAME = DM_GENERIC_ADMIN_NAME
    BUYER_INVITE_MANAGER_CONFIRMATION_SUBJECT = 'Digital Marketplace buyer account request'
    BUYER_INVITE_MANAGER_CONFIRMATION_NAME = DM_GENERIC_ADMIN_NAME

    SELLER_NEW_OPPORTUNITY_EMAIL_SUBJECT = 'Digital Marketplace - new business opportunity'
    SELLER_NEW_OPPORTUNITY_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL

    CREATE_USER_SUBJECT = 'Create your Digital Marketplace account'
    SECRET_KEY = None
    SHARED_EMAIL_KEY = None
    RESET_PASSWORD_SALT = 'ResetPasswordSalt'
    INVITE_EMAIL_SALT = 'InviteEmailSalt'
    BUYER_CREATION_TOKEN_SALT = 'BuyerCreation'

    ASSET_PATH = URL_PREFIX + '/static'

    # Throw an exception in dev when a feature flag is used in code but not defined.
    RAISE_ERROR_ON_MISSING_FEATURES = True
    # List all your feature flags below
    FEATURE_FLAGS = {
        'BRIEF_FILTER': True,
        'BRIEF_PDF': True,
        'SUPPLIERS_VIEW_OWN_PAGE': True,
    }

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
    CSRF_FAKED = True

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"

    SECRET_KEY = 'TestKeyTestKeyTestKeyTestKeyTestKeyTestKeyX='
    SHARED_EMAIL_KEY = SECRET_KEY
    SERVER_NAME = 'localhost'


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    DM_SEARCH_PAGE_SIZE = 5

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_DEFAULT_CACHE_MAX_AGE = 60

    SECRET_KEY = 'DevKeyDevKeyDevKeyDevKeyDevKeyDevKeyDevKeyX='
    SHARED_EMAIL_KEY = SECRET_KEY


class Live(Config):
    """Base config for deployed environments"""
    DEBUG = False
    DM_HTTP_PROTO = 'https'
    DM_GA_CODE = 'UA-72722909-5'
    DM_CACHE_TYPE = 'prod'

    # If a feature flag is used in code but not defined in prod, assume it is False.
    RAISE_ERROR_ON_MISSING_FEATURES = False
    # List all your feature flags below
    FEATURE_FLAGS = {
        'BRIEF_FILTER': False,
        'BRIEF_PDF': False,
        'SUPPLIERS_VIEW_OWN_PAGE': False,
    }


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
