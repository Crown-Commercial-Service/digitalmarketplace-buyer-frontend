'''
Fields for WTForms used in the Digital Marketplace frontend
'''

from wtforms import Field, Form, FormField, RadioField
from wtforms.fields import IntegerField
from wtforms.utils import unset_value

import datetime


class DMFormField(FormField):
    '''
    A wrapper for `wtforms.FormField`
    '''
    @property
    def errors(self):
        '''The validation errors, in a format suitable for frontend-toolkit'''
        return [e for errors in self.form.errors.values() for e in errors]


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
    A field enclosure for a date entry fieldset

    >>> from wtforms import Form
    >>> from werkzeug.datastructures import MultiDict
    >>> class DateForm(Form):
    ...     date = DateField()
    >>> form = DateForm(MultiDict({
    ...     'date-day': '31',
    ...     'date-month': '12',
    ...     'date-year': '1999'}))
    >>> form.date.data
    datetime.date(1999, 12, 31)
    '''

    class _DateForm(Form):
        day = IntegerField("Day")
        month = IntegerField("Month")
        year = IntegerField("Year")

    def __init__(self, label=None, validators=None, separator='-', **kwargs):
        super().__init__(label=label, validators=validators, **kwargs)
        self.form_field = FormField(self._DateForm, separator=separator, **kwargs)

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        else:
            return {}

    def process(self, formdata, data=unset_value):
        '''
        Process incoming data.

        Overrides wtforms.Field.process.

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
        self.raw_data = [raw_data]

        try:
            self.data = datetime.date(**self.form_field.data)
        except (TypeError, ValueError):
            self.data = None
            self.process_errors.append(self.gettext('Not a valid date value'))
