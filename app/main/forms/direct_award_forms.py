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


class WhyDidYouNotAwardForm(FlaskForm):
    why_did_you_not_award_the_contract = RadioField(
        "Why didn't you award a contract?",
        validators=[InputRequired(message="Please select a reason why you didn't award a contract")]
    )

    def __init__(self, *args, **kwargs):
        super(WhyDidYouNotAwardForm, self).__init__(*args, **kwargs)

        options = [
            {
                "label": "The work has been cancelled",
                "value": "work_cancelled",
                "description": "For example, because you no longer have the budget",
            },
            {
                "label": "There were no suitable services",
                "value": "no_suitable_services",
                "description": "The services in your search results did not meet your requirements",
            },
        ]

        self.why_did_you_not_award_the_contract.choices = [(option['value'], option['label']) for option in options]
        self.why_did_you_not_award_the_contract.options = options
