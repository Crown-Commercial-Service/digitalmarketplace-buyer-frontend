from flask_wtf import Form
from wtforms.validators import Length
from dmutils.forms import StripWhitespaceStringField, StringField

class CreateProjectForm(Form):
    name = StripWhitespaceStringField(
        'Name your search', id="project_name",
        validators=[
            Length(min=1,
                   max=100,
                   message="Names must be between 1 and 100 characters")
        ]
    )
