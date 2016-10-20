# coding: utf-8
import mock
import pytest
from lxml import html

from ...helpers import BaseApplicationTest


@mock.patch('app.main.suppliers.DataAPIClient')
class TestCaseStudyPage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.DataAPIClient'
        ).start()

        self.case_study = self._get_case_study_fixture_data()

    def teardown(self):
        self._data_api_client.stop()

    def test_case_study_page_requires_login(self, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    def test_arbitrary_suppliers_not_allowed_to_see_case_study(self, api_client):
        self.login_as_supplier(supplier_code=1234)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    @pytest.mark.skip(reason="FIXME stub out react rendering")
    def test_suppliers_can_see_own_case_study_page(self, api_client):
        self.login_as_supplier(supplier_code=1)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        assert len(document.xpath('//div[@id="react-bundle-casestudy-view-state"]')) > 0

    @pytest.mark.skip(reason="FIXME stub out react rendering")
    def test_should_have_supplier_details_on_supplier_page(self, api_client):
        self.login_as_buyer()
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        assert document.xpath('//h2')[0].text.strip() == 'Gizmo Refactoring'
