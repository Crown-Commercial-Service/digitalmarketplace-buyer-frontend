from datetime import timedelta

from flask import current_app, session
from wtforms import PasswordField, Form
from wtforms.csrf.session import SessionCSRF
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from dmutils.forms import StripWhitespaceStringField, StringField


class StripWhitespaceStringField(StripWhitespaceStringField):
    # WTForm errors when kwargs are passed from template contains dashes. As some html attributes needs to contain
    # dashes, following piece of code helps.
    # {{ form.email_address(extra_aria_describedby="here") }} will output the attribute aria-describedby="here"
    def __call__(self, **kwargs):
        print list(kwargs)
        for key in list(kwargs):
            if key.startswith('extra_'):
                kwargs[key[6:].replace('_', '-')] = kwargs.pop(key)
        return super(StripWhitespaceStringField, self).__call__(**kwargs)


class DmForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = None
        csrf_time_limit = None

        @property
        def csrf_context(self):
            return session

    def __init__(self, *args, **kwargs):
        if current_app.config['CSRF_ENABLED']:
            self.Meta.csrf_secret = current_app.config['SECRET_KEY']
            self.Meta.csrf_time_limit = timedelta(seconds=current_app.config['CSRF_TIME_LIMIT'])
        else:
            self.Meta.csrf = False
            self.Meta.csrf_class = None
        super(DmForm, self).__init__(*args, **kwargs)


class LoginForm(DmForm):
    email_address = StripWhitespaceStringField(
        'Email', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            Regexp("^[^@^\s]+@[^@^\.^\s]+(\.[^@^\.^\s]+)+$",
                   message="You must provide a valid email address")
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
            Regexp("^[^@^\s]+@[^@^\.^\s]+(\.[^@^\.^\s]+)+$",
                   message="You must provide a valid email address")
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
