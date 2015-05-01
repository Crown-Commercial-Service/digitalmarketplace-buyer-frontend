from flask import Flask
from flask.ext.bootstrap import Bootstrap
from config import config
from dmutils import apiclient, logging

from .helpers.questions import QuestionsLoader
from .presenters.search_presenters import SearchFilters


bootstrap = Bootstrap()
data_api_client = apiclient.DataAPIClient()
search_api_client = apiclient.SearchAPIClient()


def create_app(config_name):
    application = Flask(__name__)
    application.config.from_object(config[config_name])
    config[config_name].init_app(application)
    g6_questions = QuestionsLoader(
        manifest="app/helpers/questions_manifest.yml",
        questions_dir="bower_components/digital-marketplace-ssp-content/g6/"
    )
    filter_groups = SearchFilters.get_filter_groups_from_questions(
        g6_questions.sections
    )

    bootstrap.init_app(application)
    logging.init_app(application)
    data_api_client.init_app(application)
    search_api_client.init_app(application)

    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)

    main_blueprint.config = {
        'BASE_TEMPLATE_DATA': application.config['BASE_TEMPLATE_DATA'],
        'LOTS': {
            'IaaS': 'Infrastructure as a Service',
            'PaaS': 'Platform as a Service',
            'SaaS': 'Software as a Service',
            'SCS': 'Specialist Cloud Services'
        },
        'FILTER_GROUPS': filter_groups
    }

    return application
