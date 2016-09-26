from wtforms import RadioField
from wtforms.validators import DataRequired
from dmutils.forms import DmForm


class WorkOrderSellerForm(DmForm):
    seller = RadioField(
        coerce=int,
        validators=[
            DataRequired(message='You must select a seller.')
        ]
    )

    def __init__(self, *args, **kwargs):
        super(WorkOrderSellerForm, self).__init__(*args, **kwargs)

        brief_id = kwargs.pop('brief_id')
        data_api_client = kwargs.pop('data_api_client')
        responses = data_api_client.find_brief_responses(brief_id)
        self.seller.choices = [(br['supplierCode'], br['supplierName']) for br in responses['briefResponses']]
