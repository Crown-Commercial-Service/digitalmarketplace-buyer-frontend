from flask_wtf import FlaskForm
from wtforms.fields import RadioField
from wtforms.validators import Length, Optional, InputRequired

from dmutils.forms import StripWhitespaceStringField


class CreateProjectForm(FlaskForm):
    name = StripWhitespaceStringField(
        'Name your search', id="project_name",
        validators=[
            Length(min=1,
                   max=100,
                   message="Names must be between 1 and 100 characters"),
            Optional()
        ]
    )


class DidYouAwardAContractForm(FlaskForm):
    did_you_award_a_contract = RadioField(
        "Did you award a contract?",
        validators=[InputRequired(message="You need to answer this question.")],
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('still-assessing', 'We are still assessing services')
        ]
    )
