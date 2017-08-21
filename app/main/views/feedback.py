import requests

from werkzeug.exceptions import ServiceUnavailable
from werkzeug.datastructures import MultiDict
from werkzeug.urls import url_parse

from flask import current_app, request, redirect, flash, Markup

from .. import main


@main.route('/feedback', methods=["POST"])
def send_feedback():
    feedback_config = current_app.config['DM_FEEDBACK_FORM']
    form_data = MultiDict()
    for field, google_form_field in feedback_config['fields'].items():
        form_data.setlist(google_form_field, request.form.getlist(field))

    result = requests.post(feedback_config['uri'], list(form_data.items(multi=True)))
    if result.status_code != 200:
        raise ServiceUnavailable('Google forms submission problem (status %d)'.format(result.status_code))
    came_from = url_parse(request.form['uri'])
    # strip netloc and scheme as we should ignore attempts to make us redirect elsewhere
    replaced = came_from._replace(scheme='', netloc='')

    flash(Markup(
        """Thank you for your message. If you have more extensive feedback, please
        <a href="mailto:enquiries@digitalmarketplace.service.gov.uk">email us</a> or
        <a href="https://airtable.com/shrkFM8L6Wfenzn5Q">take part in our research</a>.
        """))

    return redirect(replaced, code=303)
