import re

from wtforms import Form
from wtforms import PasswordField
from wtforms.fields.core import BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from dmutils.forms import StripWhitespaceStringField, StringField

from app.helpers.form_helpers import DmForm


email_regex = Regexp(r'^[^@^\s]+@[\d\w-]+(\.[\d\w-]+)+$',
                     flags=re.UNICODE,
                     message='You must provide a valid email address')


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
