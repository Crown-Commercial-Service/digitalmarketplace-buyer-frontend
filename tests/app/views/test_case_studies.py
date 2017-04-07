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


@mock.patch('app.main.suppliers.data_api_client')
@mock.patch('app.main.suppliers.DataAPIClient')
@mock.patch('app.main.suppliers.render_component')
class TestCaseStudyCreatePage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyCreatePage, self).setup()

        self.case_study = self._get_case_study_fixture_data()
        self.domain = {u'domain': {u'ordering': 1,
                                   u'id': 1,
                                   u'links': {u'self': u'http://localhost:5000/domains/1'},
                                   u'name': u'Strategy and Policy'}
                       }

    def test_new_case_study_page_renders(self, render_component, api_client, data_api_client):
        api_client.return_value.get_case_study.return_value = self.case_study
        data_api_client.return_value.req.return_value.domain.return_value.get.return_value = self.domain
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'

        with self.app.app_context():
            self.login_as_supplier(1)

            res = self.client.get(self.expand_path(
                '/case-study/create/1/brief/1'
                )
            )

            # assert FakeCsrf.valid_token in res.get_data(as_text=True)
            assert res.status_code == 200

    def test_create_new_case_study(self, render_component, api_client, data_api_client):
        self.login_as_supplier(1)
        data_api_client.return_value.req.return_value.domain.return_value.get.return_value = self.domain
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'
        data = test_case_study
        data['csrf_token'] = FakeCsrf.valid_token
        res = self.client.post(
            self.expand_path(
                '/case-study/create/1/brief/1'
            ),
            data=data)

        assert res.status_code == 302
        assert '/sellers/opportunities/1/assessment' in res.location


@mock.patch('app.main.suppliers.DataAPIClient')
@mock.patch('app.main.suppliers.render_component')
class TestCaseStudyEditPage(BaseApplicationTest):
    def setup(self):
        super(TestCaseStudyEditPage, self).setup()

        self.case_study = self._get_case_study_fixture_data()

    def test_edit_case_study_page_renders(self, render_component, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'
        self.login_as_supplier(1)

        res = self.client.get(self.expand_path(
            '/case-study/1/update'
        )
        )

        # assert FakeCsrf.valid_token in res.get_data(as_text=True)
        assert res.status_code == 200

    def test_edit_case_study(self, render_component, api_client):
        api_client.return_value.get_case_study.return_value = self.case_study
        render_component.return_value.get_props.return_value = {}
        render_component.return_value.get_slug.return_value = 'slug'
        self.login_as_supplier(1)

        data = test_case_study
        data['csrf_token'] = FakeCsrf.valid_token
        res = self.client.post(
            self.expand_path(
                '/case-study/1/update'
            ),
            data=data)

        assert res.status_code == 302
