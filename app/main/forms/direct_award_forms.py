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


# TODO: move this into dmutils.forms
class DMRadioField(RadioField):
    @property
    def options(self):
        """The RadioField choices in a format suitable for the frontend toolkit"""
        return [{"label": label, "value": value} for value, label in self.choices]


class DidYouAwardAContractForm(FlaskForm):
    YES = 'yes'
    NO = 'no'
    STILL_ASSESSING = 'still-assessing'

    did_you_award_a_contract = DMRadioField(
        "Did you award a contract?",
        validators=[InputRequired(message="You need to answer this question.")],
        choices=[
            (YES, 'Yes'),
            (NO, 'No'),
            (STILL_ASSESSING, 'We are still assessing services')
        ]
    )
