from wtforms import RadioField
from wtforms.validators import DataRequired
from dmutils.forms import DmForm, StripWhitespaceStringField
from wtforms import TextAreaField
from work_order_data import questions


class WorkOrderSellerForm(DmForm):
    seller = RadioField(
        coerce=int,
        validators=[
            DataRequired(message='You must select a seller.')
        ]
    )

    def __init__(self, brief_id, data_api_client, *args, **kwargs):
        super(WorkOrderSellerForm, self).__init__(*args, **kwargs)

        responses = data_api_client.find_brief_responses(brief_id)
        choices = []
        supplier_codes = []
        for br in responses['briefResponses']:
            supplier_code = br['supplierCode']
            if supplier_code not in supplier_codes:
                choices.append({
                    'supplier_code': supplier_code,
                    'supplier_name': br['supplierName']
                })
                supplier_codes.append(supplier_code)

        self.seller.choices = [(br['supplier_code'], br['supplier_name']) for br in choices]


def FormFactory(slug, formdata=None):
    class WorkOrderQuestionForm(DmForm):
        heading = questions[slug]['heading']
        summary = questions[slug]['summary']

    type = questions[slug].get('type', None)
    if type == 'text':
        setattr(WorkOrderQuestionForm, slug, StripWhitespaceStringField(
            questions[slug]['label'],
            validators=[DataRequired(message=questions[slug]['message'])]
        ))
    elif type == 'address':
        setattr(WorkOrderQuestionForm, 'name', StripWhitespaceStringField(
            questions[slug]['nameLabel'],
            validators=[DataRequired(message=questions[slug]['nameMessage'])]))
        setattr(WorkOrderQuestionForm, 'contact', StripWhitespaceStringField(
            questions[slug]['contactLabel'],
            validators=[DataRequired(message=questions[slug]['contactMessage'])]))
        setattr(WorkOrderQuestionForm, 'abn', StripWhitespaceStringField(
            questions[slug]['abnLabel'],
            validators=[DataRequired(message=questions[slug]['abnMessage'])]))
    else:
        setattr(WorkOrderQuestionForm, slug, TextAreaField(
            questions[slug]['label'],
            validators=[DataRequired(message=questions[slug]['message'])]
        ))

    return WorkOrderQuestionForm(formdata=formdata)
