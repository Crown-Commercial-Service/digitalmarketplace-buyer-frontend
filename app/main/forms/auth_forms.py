from flask_wtf import Form
from wtforms import PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from dmutils.forms import StripWhitespaceStringField, StringField


class LoginForm(Form):
    email_address = StripWhitespaceStringField(
        'Email address', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            Email(message="You must provide a valid email address")
        ]
    )
    password = PasswordField(
        'Password', id="input_password",
        validators=[
            DataRequired(message="You must provide your password")
        ]
    )


class EmailAddressForm(Form):
    email_address = StripWhitespaceStringField(
        'Email address', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            Email(message="You must provide a valid email address")
        ]
    )


class ChangePasswordForm(Form):
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


class CreateUserForm(Form):
    name = StripWhitespaceStringField(
        'Your name', id="input_name",
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
            Regexp("^$|^\\+?([\\d\\s()-]){6,20}$",
                   message="Phone numbers must be between 6 and 20 characters."
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
