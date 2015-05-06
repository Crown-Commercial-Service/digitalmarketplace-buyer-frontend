from flask import Flask
from flask.ext.bootstrap import Bootstrap
from config import config
from dmutils import apiclient, logging


bootstrap = Bootstrap()
data_api_client = apiclient.DataAPIClient()
search_api_client = apiclient.SearchAPIClient()


def create_app(config_name):

    application = Flask(__name__)
    application.config.from_object(config[config_name])
    config[config_name].init_app(application)

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
        'SEARCH_FILTERS': [
            {
                'legend': 'Service features and management',
                'filters': [
                    {
                        'label': 'Self-service provisioning supported',
                        'name': 'selfserviceprovisioning',
                        'isBoolean': True
                    },
                    {
                        'label': 'Offline working and syncing supported',
                        'name': 'offlineWorking',
                        'isBoolean': True
                    },
                    {
                        'label': 'Real-time management information available',
                        'name': 'analyticsAvailable',
                        'isBoolean': True
                    },
                    {
                        'label': 'Elastic cloud approach supported',
                        'name': 'elasticCloud',
                        'isBoolean': True
                    },
                    {
                        'label': 'Guaranteed resources defined',
                        'name': 'guaranteedResources',
                        'isBoolean': True
                    },
                    {
                        'label': 'Persistent storage supported',
                        'name': 'persistentStorage',
                        'isBoolean': True
                    }
                ]
            }
        ]
    }

    return application
