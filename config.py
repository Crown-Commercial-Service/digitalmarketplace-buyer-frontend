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
    DEBUG = False
    ASSET_PATH = '/static/'
    BASE_TEMPLATE_DATA = {
        'header_class': 'with-proposition',
        'asset_path': ASSET_PATH,
        'asset_fingerprinter': AssetFingerprinter(asset_root=ASSET_PATH)
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
    FEATURE_FLAGS_SUPPLIER_A_TO_Z = False
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = False
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = False
    FEATURE_FLAGS_G_CLOUD_7_SUPPLIER_GUIDE = False

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
    FEATURE_FLAGS_SUPPLIER_A_TO_Z = enabled_since('2015-07-08')
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = enabled_since('2015-08-03')
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = enabled_since('2015-08-03')
    FEATURE_FLAGS_G_CLOUD_7_SUPPLIER_GUIDE = enabled_since('2015-08-03')


class Development(Config):
    DEBUG = True

    DM_SEARCH_PAGE_SIZE = 5
    FEATURE_FLAGS_SUPPLIER_A_TO_Z = enabled_since('2015-07-08')
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = enabled_since('2015-08-03')
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = enabled_since('2015-08-03')
    FEATURE_FLAGS_G_CLOUD_7_SUPPLIER_GUIDE = enabled_since('2015-08-03')


class Preview(Config):
    FEATURE_FLAGS_SUPPLIER_A_TO_Z = enabled_since('2015-07-08')
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = enabled_since('2015-08-03')
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = enabled_since('2015-08-03')


class Live(Config):
    DEBUG = False
    FEATURE_FLAGS_SUPPLIER_A_TO_Z = enabled_since('2015-07-30')
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = enabled_since('2015-08-20')
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = enabled_since('2015-09-01')


class Staging(Live):
    FEATURE_FLAGS_G_CLOUD_7_NOTICE = enabled_since('2015-08-18')
    FEATURE_FLAGS_G_CLOUD_7_IS_LIVE = enabled_since('2015-09-01')

configs = {
    'development': Development,
    'preview': Preview,
    'staging': Staging,
    'production': Live,
    'test': Test,
}
