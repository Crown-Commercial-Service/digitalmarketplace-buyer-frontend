from wtforms import PasswordField
from wtforms.fields.core import RadioField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from dmutils.forms import StripWhitespaceStringField, StringField, DmForm, email_validator, government_email_validator

from app import data_api_client


class LoginForm(DmForm):
    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            email_validator,
        ]
    )
    password = PasswordField(
        'Password', id="input_password",
        validators=[
            DataRequired(message="You must provide your password")
        ]
    )


class EmailAddressForm(DmForm):
    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            email_validator,
        ]
    )


class BuyerSignupForm(DmForm):
    employment_status = RadioField(
        label='I am a public service employee or have authorisation, as described above.',
        choices=[
            ('employee', 'I am an employee under the Commonwealth Public Service Act (1999) or under equivalent state or territory legislation and need access to the Digital Marketplace to perform my role.'),  # noqa
            ('contractor', 'I am a contractor working in local, state or federal government.'),
        ],
        validators=[
            DataRequired(message='You must specify your employment status')
        ]
    )

    name = StripWhitespaceStringField(
        'Your full name', id='name',
        validators=[
            DataRequired(message='You must provide your full name'),
        ]
    )

    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message='You must provide an email address'),
            government_email_validator,
        ]
    )


class BuyerInviteRequestForm(BuyerSignupForm):

    manager_name = StripWhitespaceStringField(
        'Manager name', id='manager_name',
        validators=[
            DataRequired(message='You must provide the name of your manager'),
        ]
    )

    manager_email = StripWhitespaceStringField(
        'Manager email address', id='manager_email',
        validators=[
            DataRequired(message='You must provide your manager\'s email address'),
            government_email_validator,
        ]
    )


class ChangePasswordForm(DmForm):
    password = PasswordField(
        'Password', id="input_password",
        validators=[
            DataRequired(message="You must enter a new password"),
            Length(min=10,
                   max=50,
                   message="Passwords must be between 10 and 50 characters"
                   )
        ]
    )
    confirm_password = PasswordField(
        'Confirm password', id="input_confirm_password",
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo('password', message="The passwords you entered do not match")
        ]
    )


class CreateUserForm(DmForm):

    name = StripWhitespaceStringField(
        'Full name', id="input_name",
        validators=[
            DataRequired(message="You must enter a name"),
            Length(min=1,
                   max=255,
                   message="Names must be between 1 and 255 characters"
                   )
        ]
    )

    password = PasswordField(
        'Password', id="input_password",
        validators=[
            DataRequired(message="You must enter a password"),
            Length(min=10,
                   max=50,
                   message="Passwords must be between 10 and 50 characters"
                   )
        ]
    )

    accept = BooleanField(
        validators=[
            DataRequired(message="You must accept the terms and conditions")
        ]
    )
