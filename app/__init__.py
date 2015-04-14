from flask import Flask
from flask.ext.bootstrap import Bootstrap
from config import config
from .helpers.questions import QuestionsLoader


bootstrap = Bootstrap()


def create_app(config_name):

    application = Flask(__name__)
    application.config.from_object(config[config_name])
    config[config_name].init_app(application)
    questions = QuestionsLoader(
        "app/helpers/content_manifest.yml",
        "bower_components/digital-marketplace-ssp-content/g6/"
    )

    bootstrap.init_app(application)

    from .main import main as main_blueprint
    application.register_blueprint(main_blueprint)
    main_blueprint.config = {
        'BASE_TEMPLATE_DATA': application.config['BASE_TEMPLATE_DATA'],
        'LOTS': {
            'IaaS': 'Infrastructure as a Service',
            'PaaS': 'Platform as a Service',
            'SaaS': 'Software as a Service',
            'SCS': 'Specialist Cloud Services'
        },
        'SEARCH_FILTERS': questions.sections
    }

    return application
