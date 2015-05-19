from flask import Flask, request, redirect
from flask.ext.bootstrap import Bootstrap
from config import configs
from dmutils import apiclient, logging, config
from .helpers.questions import QuestionsLoader
from .presenters.search_presenters import SearchFilters


bootstrap = Bootstrap()
data_api_client = apiclient.DataAPIClient()
search_api_client = apiclient.SearchAPIClient()


def create_app(config_name):
    application = Flask(__name__)
    application.config.from_object(configs[config_name])
    configs[config_name].init_app(application)
    config.init_app(application)
    filter_groups = SearchFilters.get_filter_groups_from_questions(
        manifest="app/helpers/questions_manifest.yml",
        questions_dir="bower_components/digital-marketplace-ssp-content/g6/"
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

    @application.before_request
    def remove_trailing_slash():
        if request.path != '/' and request.path.endswith('/'):
            return redirect(request.path[:-1], code=301)

    return application
