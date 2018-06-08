'''
Validators for WTForms used in the Digital Marketplace frontend
'''

from wtforms import ValidationError


__all__ = ['GreaterThan', 'Y2K']


class GreaterThan:
    """
    Compares the values of two fields.

    :param fieldname:
        The name of the other field to compare to.

    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(field.gettext("Invalid field name '%s'." % self.fieldname))
        if other.data and not field.data > other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname
            }
            message = self.message
            if message is None:
                message = field.gettext('Field must be greater than %(other_name)s.')

            raise ValidationError(message % d)


class Y2K:
    """
    Prepare for the 21st Century.

    Validates that a `DateField`'s year field has a four digit year value.

    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        try:
            digits = len(field.form_field.year.raw_data[0])
        except KeyError:
            digits = 0

        if not digits == 4:
            message = self.message
            if message is None:
                message = field.gettext("Year must be YYYY.")

            raise ValidationError(message)
