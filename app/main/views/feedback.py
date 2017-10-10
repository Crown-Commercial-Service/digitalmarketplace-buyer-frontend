import requests

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
        current_app.logger.error("Feedback form submission error - unexpected response {} from {}.".format(
            result.status_code, feedback_config['uri']))
        current_app.logger.warning("Feedback message was not correctly recorded: {}".format(
            ' / '.join(request.form.values())))

    came_from = url_parse(request.form['uri'])
    # strip netloc and scheme as we should ignore attempts to make us redirect elsewhere
    replaced = came_from._replace(scheme='', netloc='')

    flash(Markup(
        """Thank you for your message. If you have more detailed feedback, please email
        <a href="mailto:enquiries@digitalmarketplace.service.gov.uk">enquiries@digitalmarketplace.service.gov.uk</a> or
        <a target="_blank" rel="external noopener noreferrer" href="https://airtable.com/shrkFM8L6Wfenzn5Q">take
        part in our research</a>.
        """))

    return redirect(replaced, code=303)
