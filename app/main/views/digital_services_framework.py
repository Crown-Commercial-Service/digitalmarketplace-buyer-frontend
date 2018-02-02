from flask import abort

from ...main import main


@main.route('/digital-services/framework')
def framework_digital_services():
    abort(410)
