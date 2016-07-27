from flask_wtf import Form
from wtforms import IntegerField, SelectMultipleField
from wtforms.validators import NumberRange


class BriefSearchForm(Form):
    page = IntegerField(default=1, validators=(NumberRange(min=1),))
    status = SelectMultipleField("Status", choices=(
        ("live", "Open",),
        ("closed", "Closed",)
    ))
    # lot choices expected to be set at runtime
    lot = SelectMultipleField("Category")

    def __init__(self, *args, **kwargs):
        """
            Requires extra keyword arguments:
             - `framework` - information on the target framework as returned by the api
             - `data_api_client` - a data api client (should be able to remove the need for this arg at some point)
        """
        super(BriefSearchForm, self).__init__(*args, **kwargs)
        try:
            # popping this kwarg so we don't risk it getting fed to wtforms default implementation which might use it
            # as a data field if there were a name collision
            framework = kwargs.pop("framework")
            self._framework_slug = framework["slug"]
            self.lot.choices = tuple((lot["slug"], lot["name"],) for lot in framework["lots"] if lot["allowsBrief"])
        except KeyError:
            raise TypeError("Expected keyword argument 'framework' with framework information")
        try:
            # data_api_client argument only needed so we can fit in with the current way the tests mock.patch the
            # the data_api_client directly on the view. would be nice to able to use the global reference to this
            self._data_api_client = kwargs.pop("data_api_client")
        except KeyError:
            raise TypeError("Expected keyword argument 'data_api_client'")

    def get_briefs(self):
        if not self.validate():
            raise ValueError("Will not fetch briefs for invalid form")

        statuses = self.status.data or tuple(id for id, label in self.status.choices)
        lots = self.lot.data or tuple(id for id, label in self.lot.choices)

        return self._data_api_client.find_briefs(
            status=",".join(statuses),
            lot=",".join(lots),
            framework=self._framework_slug,
            page=self.page.data,
            human=True,
        )
