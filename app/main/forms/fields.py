'''
Fields for WTForms used in the Digital Marketplace frontend
'''

from wtforms import Field, Form, FormField, RadioField
from wtforms.fields import IntegerField
from wtforms.utils import unset_value

import datetime


class DMRadioField(RadioField):
    '''
    A wrapper for `wtforms.RadioField`
    '''
    @property
    def options(self):
        '''The RadioField choices, in a format suitable for the frontend toolkit'''
        return [{"label": label, "value": value} for value, label in self.choices]


class DateField(Field):
    '''
    A date field(set) that uses a day, month and year field.

    It behaves like a WTForms.FieldForm, but it can be used
    with validators like a normal WTForms.Field.

    >>> from wtforms import Form
    >>> from wtforms.validators import DataRequired
    >>> from werkzeug.datastructures import MultiDict
    >>> formdata = MultiDict({
    ...     'date-day': '31',
    ...     'date-month': '12',
    ...     'date-year': '1999'}))
    >>> class DateForm(Form):
    ...     date = DateField(validators=[DataRequired()])
    >>> form = DateForm(formdata)
    >>> form.date.data
    datetime.date(1999, 12, 31)
    '''

    # An internal class that defines the fields that make up the DateField.
    #
    # Inheriting from wtforms.FormField has limitations on using validators.
    #
    # Instead, the DateField is composed of a wtforms.FormField that is used
    # to turn the form data into integer values, and we then grab the data.
    #
    # The FormField instance is based on this class.
    class _DateForm(Form):
        day = IntegerField("Day")
        month = IntegerField("Month")
        year = IntegerField("Year")

    def __init__(self, label=None, validators=None, separator='-', **kwargs):
        super().__init__(label=label, validators=validators, **kwargs)
        self.form_field = FormField(self._DateForm, separator=separator, **kwargs)

    def _value(self):
        '''
        Return the values that are used to display the form

        Overrides wtforms.Field._value().
        '''
        if self.raw_data:
            return self.raw_data[0]
        else:
            return {}

    def process(self, formdata, data=unset_value):
        '''
        Process incoming data.

        Overrides wtforms.Field.process().

        Filters, process_data and process_formdata are not supported.
        '''
        self.process_errors = []

        # use the FormField to process `formdata` and `data`
        self.form_field.process(formdata, data)

        # make a "fake" raw_data property from the FormField values
        # we need the raw_data property for various validators
        raw_data = {field.name: field.raw_data[0] for field in self.form_field
                    if field.raw_data}
        if not any(raw_data.values()):
            # if all fields were empty we want raw_data to be None-ish
            raw_data = {}

        # the WTForms.Field api expects .raw_data to be a list
        self.raw_data = [raw_data]

        try:
            self.data = datetime.date(**self.form_field.data)
        except (TypeError, ValueError):
            self.data = None
            self.process_errors.append(self.gettext('Not a valid date value'))
