import os
import jinja2

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    BASE_TEMPLATE_DATA = {
        'asset_path': '/static/',
        'header_class': 'with-proposition'
    }

    DM_DATA_API_URL = 'http://localhost:5000'
    DM_DATA_API_AUTH_TOKEN = 'myToken'

    # Logging
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


config = {
    'development': Development,
    'preview': Live,
    'staging': Live,
    'production': Live,
    'test': Development,
}
