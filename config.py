import os
import hashlib
from dmutils.status import enabled_since, get_version_label
import pendulum

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
    SESSION_COOKIE_SAMESITE = 'Lax'

    PERMANENT_SESSION_LIFETIME = 36*3600

    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 8*3600

    DM_TIMEZONE = 'Australia/Sydney'

    DM_DATA_API_URL = None
    DM_DATA_API_AUTH_TOKEN = None
    DM_HTTP_PROTO = 'http'
    DM_DEFAULT_CACHE_MAX_AGE = 24*3600
    DM_EMAIL_RETURN_ADDRESS = None
    DM_SEND_EMAIL_TO_STDERR = False
    DM_CACHE_TYPE = 'dev'

    # matches api(s)
    DM_SEARCH_PAGE_SIZE = 100

    DM_GA_CODE = 'UA-72722909-6'

    # This is just a placeholder
    ES_ENABLED = True

    DEBUG = False

    DM_TEAM_EMAIL = None
    DM_TEAM_SLACK_WEBHOOK = None

    DM_GENERIC_NOREPLY_EMAIL = 'no-reply@marketplace.digital.gov.au'
    DM_GENERIC_ADMIN_NAME = 'Digital Marketplace Admin'

    DM_GENERIC_SUPPORT_EMAIL = 'marketplace@digital.gov.au'
    DM_GENERIC_SUPPORT_NAME = 'Digital Marketplace'

    RESET_PASSWORD_EMAIL_NAME = DM_GENERIC_ADMIN_NAME
    RESET_PASSWORD_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL
    RESET_PASSWORD_EMAIL_SUBJECT = 'Reset your Digital Marketplace password [SEC=UNCLASSIFIED]'

    BUYER_INVITE_REQUEST_SUBJECT = 'Buyer Account Invite Request [SEC=UNCLASSIFIED]'
    BUYER_INVITE_REQUEST_ADMIN_EMAIL = 'marketplace+buyer-request@digital.gov.au'
    BUYER_INVITE_REQUEST_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL
    BUYER_INVITE_REQUEST_EMAIL_NAME = DM_GENERIC_ADMIN_NAME
    BUYER_INVITE_MANAGER_CONFIRMATION_SUBJECT = 'Digital Marketplace buyer account request [SEC=UNCLASSIFIED]'
    BUYER_INVITE_MANAGER_CONFIRMATION_NAME = DM_GENERIC_ADMIN_NAME

    SELLER_NEW_OPPORTUNITY_EMAIL_SUBJECT = 'Digital Marketplace - new business opportunity'
    SELLER_NEW_OPPORTUNITY_EMAIL_FROM = DM_GENERIC_NOREPLY_EMAIL

    CREATE_USER_SUBJECT = 'Create your Digital Marketplace account [SEC=UNCLASSIFIED]'
    SECRET_KEY = None
    SHARED_EMAIL_KEY = None
    RESET_PASSWORD_SALT = 'ResetPasswordSalt'
    INVITE_EMAIL_SALT = 'InviteEmailSalt'
    BUYER_CREATION_TOKEN_SALT = 'BuyerCreation'
    SIGNUP_INVITATION_TOKEN_SALT = 'NewUserInviteEmail'

    ASSET_PATH = URL_PREFIX + '/static'

    # Throw an exception in dev when a feature flag is used in code but not defined.
    RAISE_ERROR_ON_MISSING_FEATURES = True
    # List all your feature flags below
    FEATURE_FLAGS = {
        'CASE_STUDY': True,
        'XLSX_EXPORT': True,
        'SELLER_REGISTRATION': True,
        'DM_FRAMEWORK': True,
        'TEAM_VIEW': True
    }

    # LOGGING
    DM_LOG_LEVEL = 'DEBUG'
    DM_LOG_PATH = None
    DM_APP_NAME = 'buyer-frontend'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Vcap-Request-Id'

    REACT_BUNDLE_URL = 'https://dm-dev-frontend.apps.y.cld.gov.au/bundle/'
    REACT_RENDER_URL = 'https://dm-dev-frontend.apps.y.cld.gov.au/render'
    REACT_RENDER = not DEBUG

    ROLLBAR_TOKEN = None
    S3_BUCKET_NAME = None
    S3_ENDPOINT_URL = 's3-ap-southeast-2.amazonaws.com'
    AWS_DEFAULT_REGION = None

    GENERIC_EMAIL_DOMAINS = ['bigpond.com', 'digital.gov.au', 'gmail.com', 'hotmail.com', 'icloud.com',
                             'iinet.net.au', 'internode.on.net', 'live.com.au', 'me.com', 'msn.com',
                             'optusnet.com.au', 'outlook.com', 'outlook.com.au', 'ozemail.com.au',
                             'yahoo.com', 'yahoo.com.au']

    MULTI_CANDIDATE_PUBLISHED_DATE = pendulum.create(2018, 4, 17)


class Test(Config):
    DEBUG = True
    DM_LOG_LEVEL = 'CRITICAL'
    CSRF_ENABLED = False
    CSRF_FAKED = True

    DM_DATA_API_URL = "http://localhost:5000/api/"
    DM_DATA_API_AUTH_TOKEN = "myToken"

    # Used a fixed timezone for tests. Using Sydney timezone will catch more timezone bugs than London.
    DM_TIMEZONE = 'Australia/Sydney'

    SECRET_KEY = 'TestKeyTestKeyTestKeyTestKeyTestKeyTestKeyX='
    SHARED_EMAIL_KEY = SECRET_KEY
    SERVER_NAME = 'localhost'

    FEATURE_FLAGS = {
        'CASE_STUDY': True,
        'XLSX_EXPORT': True,
        'SELLER_REGISTRATION': True,
        'DM_FRAMEWORK': False,
        'TEAM_VIEW': True
    }


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    DM_SEARCH_PAGE_SIZE = 5

    DM_DATA_API_URL = "http://localhost:5000/api/"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_DEFAULT_CACHE_MAX_AGE = 60

    SECRET_KEY = 'DevKeyDevKeyDevKeyDevKeyDevKeyDevKeyDevKeyX='
    SHARED_EMAIL_KEY = SECRET_KEY
    DM_SEND_EMAIL_TO_STDERR = True


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
        'CASE_STUDY': False,
        'XLSX_EXPORT': False,
        'SELLER_REGISTRATION': True,
        'DM_FRAMEWORK': True,
        'TEAM_VIEW': True
    }

    REACT_BUNDLE_URL = 'https://dm-frontend.apps.b.cld.gov.au/bundle/'
    REACT_RENDER_URL = 'https://dm-frontend.apps.b.cld.gov.au/render'
    REACT_RENDER = True


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
