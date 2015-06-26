from flask import Flask, request, redirect
from flask.ext.bootstrap import Bootstrap
from config import configs
from dmutils import apiclient, init_app, flask_featureflags
from dmutils.content_loader import ContentLoader


bootstrap = Bootstrap()
data_api_client = apiclient.DataAPIClient()
search_api_client = apiclient.SearchAPIClient()
feature_flags = flask_featureflags.FeatureFlag()


def create_app(config_name):
    application = Flask(__name__)

    init_app(
        application,
        configs[config_name],
        bootstrap=bootstrap,
        data_api_client=data_api_client,
        feature_flags=feature_flags,
        search_api_client=search_api_client
    )

    questions_builder = ContentLoader(
        "app/helpers/questions_manifest.yml",
        "app/content/g6/"
    ).get_builder()

    from .main import main as main_blueprint
    from .status import status as status_blueprint

    application.register_blueprint(status_blueprint)
    application.register_blueprint(main_blueprint)

    main_blueprint.config = {
        'BASE_TEMPLATE_DATA': application.config['BASE_TEMPLATE_DATA'],
        'QUESTIONS_BUILDER': questions_builder
    }

    @application.before_request
    def remove_trailing_slash():
        if request.path != '/' and request.path.endswith('/'):
            if request.query_string:
                return redirect(
                    '{}?{}'.format(
                        request.path[:-1],
                        request.query_string.decode('utf-8')
                    ),
                    code=301
                )
            else:
                return redirect(request.path[:-1], code=301)

    return application
