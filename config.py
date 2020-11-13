import os
import jinja2
from dmutils.status import get_version_label
from dmutils.asset_fingerprint import AssetFingerprinter

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    SESSION_COOKIE_NAME = 'dm_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    DM_COOKIE_PROBE_EXPECT_PRESENT = True

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    DM_DATA_API_URL = None
    DM_DATA_API_AUTH_TOKEN = None
    DM_SEARCH_API_URL = None
    DM_SEARCH_API_AUTH_TOKEN = None
    DM_MANDRILL_API_KEY = None
    DM_REDIS_SERVICE_NAME = None

    # Used for generating absolute URLs from relative URLs when necessary
    DM_PATCH_FRONTEND_URL = 'http://localhost/'

    # matches api(s)
    DM_SEARCH_PAGE_SIZE = 100

    # This is just a placeholder
    ES_ENABLED = True

    DEBUG = False

    RESET_PASSWORD_EMAIL_NAME = 'Digital Marketplace Admin'
    RESET_PASSWORD_EMAIL_FROM = 'cloud_digital@crowncommercial.gov.uk'
    RESET_PASSWORD_EMAIL_SUBJECT = 'Reset your Digital Marketplace password'

    CREATE_USER_SUBJECT = 'Create your Digital Marketplace account'
    SECRET_KEY = None
    SHARED_EMAIL_KEY = None
    RESET_PASSWORD_SALT = 'ResetPasswordSalt'
    INVITE_EMAIL_SALT = 'InviteEmailSalt'

    ASSET_PATH = '/static/'
    BASE_TEMPLATE_DATA = {
        'header_class': 'with-proposition',
        'asset_path': ASSET_PATH,
        'asset_fingerprinter': AssetFingerprinter(asset_root=ASSET_PATH)
    }

    # LOGGING
    DM_LOG_LEVEL = 'DEBUG'
    DM_PLAIN_TEXT_LOGS = False
    DM_LOG_PATH = None
    DM_APP_NAME = 'buyer-frontend'

    #: For some frameworks (represented by the keys in this map), we store no framework content. But
    #: they work just like some other framework (represented by the values in the map) for which we do
    #: have content available. The map uses slugs to identify the framework pairs, so that we can still
    #: find the framework data we need (and so that we can avoid trying to load up framework data that
    #: isn't actually available).
    DM_FRAMEWORK_CONTENT_MAP = {
        'g-cloud-4': 'g-cloud-6',
        'g-cloud-5': 'g-cloud-6',
    }

    DM_FEEDBACK_FORM = {
        'uri': 'https://docs.google.com/a/digital.cabinet-office.gov.uk/forms/d/e/1FAIpQLSc-uXv-4VqGBipDwPhJFDpET5UrHnJpsJ5FFTn4-MBAfKeOPg/formResponse',  # noqa
        'fields': {
            'uri': 'entry.1048271701',
            'what_doing': 'entry.1348335665',
            'what_happened': 'entry.869819225',
        }
    }

    GOOGLE_SITE_VERIFICATION = None

    @staticmethod
    def init_app(app):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        digitalmarketplace_govuk_frontend = os.path.join(repo_root, "node_modules", "digitalmarketplace-govuk-frontend")
        govuk_frontend = os.path.join(repo_root, "node_modules", "govuk-frontend")
        template_folders = [
            os.path.join(repo_root, "app", "templates"),
            os.path.join(digitalmarketplace_govuk_frontend),
            os.path.join(digitalmarketplace_govuk_frontend, "digitalmarketplace", "templates"),
        ]
        jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(template_folders),
            jinja2.PrefixLoader({'govuk': jinja2.FileSystemLoader(govuk_frontend)})
        ])
        app.jinja_loader = jinja_loader


class Test(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    DM_LOG_LEVEL = 'CRITICAL'
    WTF_CSRF_ENABLED = False

    DM_DATA_API_URL = "http://wrong.completely.invalid:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_SEARCH_API_URL = "http://wrong.completely.invalid:5009"
    DM_SEARCH_API_AUTH_TOKEN = "myToken"

    DM_MANDRILL_API_KEY = 'MANDRILL'
    SHARED_EMAIL_KEY = "KEY"
    SECRET_KEY = "KEY"

    GOOGLE_SITE_VERIFICATION = "NotARealVerificationKey"


class Development(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    SESSION_COOKIE_SECURE = False
    DM_SEARCH_PAGE_SIZE = 5

    DM_DATA_API_URL = f"http://localhost:{os.getenv('DM_API_PORT', 5000)}"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_SEARCH_API_URL = f"http://localhost:{os.getenv('DM_SEARCH_API_PORT', 5009)}"
    DM_SEARCH_API_AUTH_TOKEN = "myToken"

    DM_MANDRILL_API_KEY = "not_a_real_key"
    SECRET_KEY = "verySecretKey"
    SHARED_EMAIL_KEY = "very_secret"

    GOOGLE_SITE_VERIFICATION = "NotARealVerificationKey"


class Live(Config):
    """Base config for deployed environments"""
    DEBUG = False
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'
    DM_HTTP_PROTO = 'https'

    # use of invalid email addresses with live api keys annoys Notify
    DM_NOTIFY_REDIRECT_DOMAINS_TO_ADDRESS = {
        "example.com": "success@simulator.amazonses.com",
        "example.gov.uk": "success@simulator.amazonses.com",
        "user.marketplace.team": "success@simulator.amazonses.com",
    }


class Preview(Live):
    DM_PATCH_FRONTEND_URL = 'https://www.preview.marketplace.team/'


class Staging(Live):
    DM_PATCH_FRONTEND_URL = 'https://www.staging.marketplace.team/'


class Production(Live):
    DM_PATCH_FRONTEND_URL = 'https://www.digitalmarketplace.service.gov.uk/'

    GOOGLE_SITE_VERIFICATION = "TKGSGZnfHpx1-lKOthI17ANtwk7fz3F4Sbr77I0ppO0"


configs = {
    'development': Development,
    'test': Test,

    'preview': Preview,
    'staging': Staging,
    'production': Production,
}
