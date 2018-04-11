from wtforms import IntegerField, SelectMultipleField
from wtforms.validators import NumberRange
from dmutils.forms import DmForm
import flask_featureflags


class BriefSearchForm(DmForm):
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
            raise ValueError("Invalid form")

        statuses = self.status.data or tuple(id for id, label in self.status.choices)
        lots = self.lot.data or tuple(id for id, label in self.lot.choices)

        # disable framework filtering when digital marketplace framework is live
        kwargs = {} if flask_featureflags.is_active('DM_FRAMEWORK') else {"framework": self._framework_slug}

        return self._data_api_client.find_briefs(
            status=",".join(statuses),
            lot=",".join(lots),
            page=self.page.data,
            per_page=75,
            human=True,
            **kwargs
        )

    def get_filters(self):
        """
            generate the same "filters" structure as expected by search page templates
        """
        if not self.validate():
            raise ValueError("Invalid form")

        return [
            {
                "label": field.label,
                "filters": [
                    {
                        "label": choice_label,
                        "name": field.name,
                        "id": "{}-{}".format(field.id, choice_id),
                        "value": choice_id,
                        "checked": field.data and choice_id in field.data,
                    }
                    for choice_id, choice_label in field.choices
                ],
            }
            for field in (self.lot, self.status,)
        ]

    def filters_applied(self):
        """
            returns boolean indicating whether the results are actually filtered at all
        """
        if not self.validate():
            raise ValueError("Invalid form")

        return bool(self.lot.data or self.status.data)
