# coding: utf-8
import mock
import pytest
from lxml import html
from dmutils.forms import FakeCsrf

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
class TestCaseStudyViewPage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyViewPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.DataAPIClient'
        ).start()

        self._render_component = mock.patch(
            'app.main.suppliers.render_component'
        ).start()

        self.case_study = self._get_case_study_fixture_data()

    def teardown(self):
        self._data_api_client.stop()
        self._render_component.stop()

    def test_case_study_page_requires_login(self, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    def test_arbitrary_suppliers_not_allowed_to_see_case_study(self, api_client):
        self.login_as_supplier(supplier_code=1234)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))

        assert res.status_code == 302

    def test_suppliers_can_see_own_case_study_page(self, api_client):
        self.login_as_supplier(supplier_code=1)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        # document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        # assert len(document.xpath('//div[@id="react-bundle-casestudy-view-state"]')) > 0

    def test_should_have_supplier_details_on_supplier_page(self, api_client):
        self.login_as_buyer()
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.url_for('main.get_supplier_case_study', casestudy_id=1))
        # document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        # assert document.xpath('//h2')[0].text.strip() == 'Gizmo Refactoring'


@mock.patch('app.main.suppliers.DataAPIClient')
class TestCaseStudyCreatePage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyCreatePage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.DataAPIClient'
        ).start()

        self._render_component = mock.patch(
            'app.main.suppliers.render_component'
        ).start()

        self.case_study = self._get_case_study_fixture_data()

    def teardown(self):
        self._data_api_client.stop()
        self._render_component.stop()

    def test_new_case_study_page_renders(self, data_api_client):
        with self.app.app_context():
            self.login_as_supplier(1)

            res = self.client.get(self.expand_path(
                '/case-study/create'
                )
            )

            # assert FakeCsrf.valid_token in res.get_data(as_text=True)
            assert res.status_code == 200

    def test_create_new_case_study(self, data_api_client):
        self.login_as_supplier(1)
        data = test_case_study
        data['csrf_token'] = FakeCsrf.valid_token
        res = self.client.post(
            self.expand_path(
                '/case-study/create'
            ),
            data=data)

        assert res.status_code == 302


@mock.patch('app.main.suppliers.DataAPIClient')
class TestCaseStudyEditPage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyEditPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.DataAPIClient'
        ).start()

        self._render_component = mock.patch(
            'app.main.suppliers.render_component'
        ).start()

        self.case_study = self._get_case_study_fixture_data()

    def teardown(self):
        self._data_api_client.stop()
        self._render_component.stop()

    def test_edit_case_study_page_renders(self, api_client):
        self.login_as_supplier(1)
        api_client.return_value.get_case_study.return_value = self.case_study

        res = self.client.get(self.expand_path(
            '/case-study/1/update'
        )
        )

        # assert FakeCsrf.valid_token in res.get_data(as_text=True)
        assert res.status_code == 200

    def test_edit_case_study(self, api_client):
        self.login_as_supplier(1)
        api_client.return_value.get_case_study.return_value = self.case_study

        data = test_case_study
        data['csrf_token'] = FakeCsrf.valid_token
        res = self.client.post(
            self.expand_path(
                '/case-study/1/update'
            ),
            data=data)

        assert res.status_code == 302
