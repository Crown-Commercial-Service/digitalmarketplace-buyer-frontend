from wtforms import PasswordField
from wtforms.fields.core import BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from dmutils.forms import StripWhitespaceStringField, StringField, DmForm, email_regex is_government_email

from app import data_api_client


class LoginForm(DmForm):
    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            email_regex,
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
            email_regex,
        ]
    )


class BuyerInviteRequestForm(DmForm):
    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            is_government_email(data_api_client)
        ]
    )

    government_emp_checkbox = BooleanField(label='I am a public service employee or have authorisation, \
        as described above.', validators=[DataRequired(message="You must check the checkbox")])

    name = StripWhitespaceStringField(
        'Your full name', id='name',
        validators=[
            DataRequired(message='You must provide your full name'),
        ]
    )

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
            is_government_email(data_api_client)
        ]
    )

    justification = StringField(
        '', id='justification',
    )


class BuyerSignupEmailForm(EmailAddressForm):
    government_emp_checkbox = BooleanField(label='I am a public service employee or have authorisation, \
        as described above.', validators=[DataRequired(message="You must check the checkbox")])


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

    phone_number = StringField(
        'Phone number', id="input_phone_number",
        validators=[
            Regexp("^$|^\\+?([\\d\\s()-]){9,20}$",
                   message=("Phone numbers must be at least 9 characters long. "
                            "They can only include digits, spaces, plus and minus signs, and brackets.")
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
