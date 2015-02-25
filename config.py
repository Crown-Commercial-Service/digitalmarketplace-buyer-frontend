import os
import jinja2

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    @staticmethod
    def init_app(app):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        template_folders = [
            os.path.join(repo_root, 'app/templates'),
            os.path.join(repo_root, 'govuk_template/views/layouts')
        ]
        jinja_loader = jinja2.FileSystemLoader(template_folders)
        app.jinja_loader = jinja_loader


class DevelopmentConfig(Config):
    DEBUG = True,
    BASE_TEMPLATE_DATA = {
        'asset_path': '/static/',
        'header_class': 'with-proposition'
    }

config = {
    'default': DevelopmentConfig
}
