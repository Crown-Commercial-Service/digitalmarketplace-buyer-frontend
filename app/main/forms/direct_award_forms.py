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


class WhichServiceWonTheContractForm(FlaskForm):
    which_service_won_the_contract = RadioField(
        "Which service won the contract?",
        validators=[InputRequired(message="Please select the supplier which won the contract")],
    )

    def __init__(self, services, *args, **kwargs):
        super(WhichServiceWonTheContractForm, self).__init__(*args, **kwargs)

        self.which_service_won_the_contract.choices = [
            (service["id"], service["data"]["serviceName"])
            for service in services['services']]

        self.which_service_won_the_contract.options = [{
            "label": service["data"]["serviceName"],
            "value": service["id"],
            "description": service["supplier"]["name"]
        } for service in services['services']]
