import requests

from werkzeug.exceptions import ServiceUnavailable
from werkzeug.datastructures import MultiDict
from werkzeug.urls import url_parse

from flask import current_app, request, redirect

from .. import main


@main.route('/feedback', methods=["POST"])
def send_feedback():
    feedback_config = current_app.config['DM_FEEDBACK_FORM']
    form_data = MultiDict()
    for field, google_form_field in feedback_config['fields'].items():
        form_data.setlist(google_form_field, request.form.getlist(field))

    result = requests.post(feedback_config['uri'], list(form_data.iteritems(multi=True)))
    if result.status_code != 200:
        raise ServiceUnavailable('Google forms submission problem (status %d)'.format(result.status_code))
    came_from = url_parse(request.form['uri'])
    # strip netloc and scheme as we should ignore attempts to make us redirect elsewhere
    replaced = came_from._replace(scheme='', netloc='')

    return redirect(replaced, code=303)
