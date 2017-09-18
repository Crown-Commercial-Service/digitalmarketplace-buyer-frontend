from flask_wtf import Form
from wtforms.validators import Length, Optional
from dmutils.forms import StripWhitespaceStringField


class CreateProjectForm(Form):
    name = StripWhitespaceStringField(
        'Name your search', id="project_name",
        validators=[
            Length(min=1,
                   max=100,
                   message="Names must be between 1 and 100 characters"),
            Optional()
        ]
    )
