import os
import jinja2

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    BASE_TEMPLATE_DATA = {
        'asset_path': '/static/',
        'header_class': 'with-proposition'
    }

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
    'preview': Development,
    'staging': Live,
    'production': Live,
    'test': Development,
}
