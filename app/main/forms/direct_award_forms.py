from flask_wtf import FlaskForm

from wtforms.fields import DecimalField, RadioField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, InputRequired

from dmutils.forms.fields import DateField
from dmutils.forms.validators import GreaterThan

from dmutils.forms import StripWhitespaceStringField

from decimal import Decimal


class CreateProjectForm(FlaskForm):
    name = StripWhitespaceStringField(
        'Name your search', id="project_name",
        validators=[
            Length(min=1,
                   max=100,
                   message="Names must be between 1 and 100 characters"),
            Optional(),
        ])


# TODO: move this into dmutils.forms
class DMRadioField(RadioField):
    @property
    def options(self):
        """The RadioField choices in a format suitable for the frontend toolkit"""
        return [{"label": label, "value": value} for value, label in self.choices]


class DMBooleanField(BooleanField):
    @property
    def options(self):
        # Even single boolean fields are expected to be in an 'options' list
        return [{"label": self.label.text, "value": self.data}]


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
            (STILL_ASSESSING, 'We are still assessing services'),
        ])


class WhichServiceWonTheContractForm(FlaskForm):
    which_service_won_the_contract = RadioField(
        "Which service won the contract?",
        validators=[InputRequired(message="Please select the service that won the contract")],
    )

    def __init__(self, services, *args, **kwargs):
        super(WhichServiceWonTheContractForm, self).__init__(*args, **kwargs)

        self.which_service_won_the_contract.choices = [
            (service["id"], service["data"]["serviceName"])
            for service in services['services']]

        self.which_service_won_the_contract.options = [{
            "label": service["data"]["serviceName"],
            "value": service["id"],
            "hint": service["supplier"]["name"],
        } for service in services['services']]


class TellUsAboutContractForm(FlaskForm):
    INPUT_REQUIRED_MESSAGE = "You need to answer this question."
    INVALID_DATE_MESSAGE = "Your answer must be a valid date."
    INVALID_VALUE_MESSAGE = "Enter your value in pounds and pence using numbers and decimals only" \
                            ", for example 9900.05 for 9900 pounds and 5 pence."

    start_date = DateField(
        "Start date",
        validators=[
            InputRequired(INPUT_REQUIRED_MESSAGE),
            DataRequired(INVALID_DATE_MESSAGE),
        ])

    end_date = DateField(
        "End date",
        validators=[
            InputRequired(INPUT_REQUIRED_MESSAGE),
            DataRequired(INVALID_DATE_MESSAGE),
            GreaterThan("start_date", "Your end date must be later than the start date."),
        ])

    value_in_pounds = DecimalField(
        "Value",
        validators=[
            InputRequired(INPUT_REQUIRED_MESSAGE),
            DataRequired(INVALID_VALUE_MESSAGE),
            NumberRange(min=Decimal('0.01'), message=INVALID_VALUE_MESSAGE),
        ])

    buying_organisation = StripWhitespaceStringField(
        "Organisation buying the service",
        validators=[
            InputRequired(INPUT_REQUIRED_MESSAGE)
        ])


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
                "hint": "For example, because you no longer have the budget",
            },
            {
                "label": "There were no suitable services",
                "value": "no_suitable_services",
                "hint": "The services in your search results did not meet your requirements",
            },
        ]

        self.why_did_you_not_award_the_contract.choices = [(option['value'], option['label']) for option in options]
        self.why_did_you_not_award_the_contract.options = options


class BeforeYouDownloadForm(FlaskForm):
    user_understands = DMBooleanField(
        "I understand that I cannot edit my search again after I export my results",
        validators=[InputRequired(message="Please confirm that you understand before you continue.")]
    )
