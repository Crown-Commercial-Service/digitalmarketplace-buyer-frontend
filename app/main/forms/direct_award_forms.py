from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import RadioField
from wtforms.validators import DataRequired, Length, NumberRange, InputRequired

from dmutils.forms.fields import (
    DMBooleanField,
    DMDateField,
    DMPoundsField,
    DMStripWhitespaceStringField,
)
from dmutils.forms.validators import DateValidator, GreaterThan


class CreateProjectForm(FlaskForm):
    save_search_selection = RadioField(
        id="input-save_search_selection",
        validators=[
            InputRequired("Select where to save your search result")
        ]
    )

    def __init__(self, projects, **kwargs):
        super().__init__(**kwargs)

        self.save_search_selection.choices = [(
            str(project["id"]),  # value
            project["name"] or f"Untitled project {project['id']}",  # text
        ) for project in projects]
        self.save_search_selection.choices.append((
            "new_search", "Save a new search",
        ))


class CreateNewProjectForm(FlaskForm):
    project_name = DMStripWhitespaceStringField(
        "Name your search. A reference number or short description of what you want to buy makes a good name.",
        validators=[
            Length(min=1, max=100, message="Enter a name for your search between 1 and 100 characters")
        ],
    )


class DidYouAwardAContractForm(FlaskForm):
    YES = 'yes'
    NO = 'no'
    STILL_ASSESSING = 'still-assessing'

    did_you_award_a_contract = RadioField(
        "Did you award a contract?",
        id="input-did_you_award_a_contract",
        validators=[InputRequired(message="Select if you have awarded your contract")],
        choices=[
            # value, text
            (YES, 'Yes'),
            (NO, 'No'),
            (STILL_ASSESSING, 'We are still assessing services'),
        ])


class WhichServiceWonTheContractForm(FlaskForm):
    which_service_won_the_contract = RadioField(
        "Which service won the contract?",
        id="input-which_service_won_the_contract",
        validators=[InputRequired(message="Select the service that won the contract")],
    )

    def __init__(self, services, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.which_service_won_the_contract.options = [{
            "label": service["data"]["serviceName"],
            "value": service["id"],
            "hint": service["supplier"]["name"],
        } for service in services['services']]

        self.which_service_won_the_contract.choices = [
            (o["value"], o["label"])
            for o in self.which_service_won_the_contract.options
        ]


class TellUsAboutContractForm(FlaskForm):
    INVALID_VALUE_MESSAGE = "Enter the value in pounds and pence, using numbers and decimals"

    start_date = DMDateField(
        "Start date",
        validators=[
            DateValidator("the start date"),
        ],
    )

    end_date = DMDateField(
        "End date",
        validators=[
            DateValidator("the end date"),
            GreaterThan("start_date", "End date must be after the start date"),
        ],
    )

    value_in_pounds = DMPoundsField(
        "Value",
        validators=[
            InputRequired("Enter the contract value"),
            DataRequired(INVALID_VALUE_MESSAGE),
            NumberRange(min=Decimal('0.01'), message=INVALID_VALUE_MESSAGE),
        ],
    )

    buying_organisation = DMStripWhitespaceStringField(
        "Organisation buying the service",
        hint="For example, National Audit Office or Lewisham Council",
        validators=[
            InputRequired("Enter an organisation")
        ],
    )


class WhyDidYouNotAwardForm(FlaskForm):
    why_did_you_not_award_the_contract = RadioField(
        "Why didn’t you award a contract?",
        id="input-why_did_you_not_award_the_contract",
        validators=[InputRequired(message="Select a reason why you didn't award a contract")]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.why_did_you_not_award_the_contract.options = [
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

        self.why_did_you_not_award_the_contract.choices = [
            (o["value"], o["label"])
            for o in self.why_did_you_not_award_the_contract.options
        ]


class BeforeYouDownloadForm(FlaskForm):
    user_understands = DMBooleanField(
        "I understand that I cannot edit my search after I export my results",
        id="input-user_understands",
        validators=[
            InputRequired(message="Confirm that you’ve finished editing your search")
        ],
    )
