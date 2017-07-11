# coding: utf-8
import mock

from ...helpers import BaseApplicationTest

test_case_study = {
    "acknowledge": "on",
    "title": "Case Study Title",
    "opportunity": "The opportunity",
    "client": "The Client Name",
    "timeframe": "January 2016 — June 2016",
    "approach": "The approach",
    "outcome": [
        "Outcome 1",
        "Outcome 2"
    ],
    "projectLinks": [
        "http://gov.au/"
    ]
}


@mock.patch('app.main.suppliers.DataAPIClient')
@mock.patch('app.main.suppliers.render_component')
class TestCaseStudyViewPage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyViewPage, self).setup()
        self.case_study = self._get_case_study_fixture_data()

    def test_case_study_page_requires_login(self, render_component, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    def test_arbitrary_suppliers_not_allowed_to_see_case_study(self, render_component, api_client):
        self.login_as_supplier(supplier_code=1234)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    def test_suppliers_can_see_own_case_study_page(self, render_component, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'
        self.login_as_supplier(supplier_code=1)

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        # document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        # assert len(document.xpath('//div[@id="react-bundle-casestudy-view-state"]')) > 0

    def test_should_have_supplier_details_on_supplier_page(self, render_component, api_client):
        self.login_as_buyer()
        api_client.return_value.get_case_study.return_value = self.case_study
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        # document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        # assert document.xpath('//h2')[0].text.strip() == 'Gizmo Refactoring'
