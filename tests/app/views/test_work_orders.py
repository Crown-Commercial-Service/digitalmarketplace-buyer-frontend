# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmutils.forms import FakeCsrf
from dmapiclient import HTTPError, APIError
from dmcontent.content_loader import ContentLoader
import mock
from lxml import html
import pytest

test_work_order = {
    "workOrder":
        {"additionalTerms": "test", "agency": {"abn": "1", "contact": "3", "name": "2"},
         "briefId": 221, "expenses": "dqdas", "id": 5, "number": "test23",
         "orderPeriod": "12",
         "seller": {
             "abn": "43 096 505 805",
             "contact": "Kris Crouchervdsfds",
             "name": "Adelphi Digital Consulting Group"},
         "son": "SON3364729",
         "supplierCode": 119,
         "supplierName": "Adelphi Digital Consulting Group"}
}

test_brief = {
    "briefs": {
        "id": 1234,
        "title": "I need a thing to do a thing",
        "frameworkSlug": "digital-outcomes-and-specialists",
        "frameworkName": "Digital Outcomes and Specialists",
        "lotSlug": "digital-specialists",
        "status": "draft",
        "users": [{"active": True,
                   "role": "buyer",
                   "emailAddress": "buyer@email.com",
                   "id": 123,
                   "name": "Buyer User"}],
        "createdAt": "2016-03-29T10:11:12.000000Z",
        "updatedAt": "2016-03-29T10:11:13.000000Z",
        "clarificationQuestions": [],
        "summary": "test summary",
        "contractLength": "6 months",
        "additionalTerms": "some terms",
        "securityClearance": "I have clearance",
    }
}


@mock.patch('app.buyers.views.work_orders.data_api_client')
class TestSelectSellerForWorkOrder(BaseApplicationTest):
    def test_start_work_order_page_renders(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = test_brief
            data_api_client.find_brief_responses.return_value = {
                'briefResponses': [
                    {
                        'supplierCode': 1234,
                        'supplierName': 'test supplier'
                    }
                ]
            }

            res = self.client.get(self.expand_path(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
                '/work-orders/create')
            )

            assert FakeCsrf.valid_token in res.get_data(as_text=True)
            assert res.status_code == 200

    def test_404_if_brief_incorrect(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = {'briefs': {'frameworkSlug': 'xxxx', 'lotSlug': 'yyyyy'}}
            res = self.client.get(self.expand_path(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
                '/work-orders/create')
            )

            assert res.status_code == 404


@mock.patch('app.buyers.views.work_orders.data_api_client')
class TestCreateNewWorkOrder(BaseApplicationTest):
    def test_create_new_work_order(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.find_brief_responses.return_value = {
            'briefResponses': [
                {
                    'supplierCode': 4321,
                    'supplierName': 'test supplier'
                }
            ]
        }
        data_api_client.get_supplier.return_value = {
            'supplier': {
                'abn': '123456',
                'name': 'test supplier',
                'contacts': [{
                    'name': 'joe bloggs'
                }]
            }
        }

        res = self.client.post(
            self.expand_path(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
                '/work-orders/create'
            ),
            data={
                'seller': 4321,
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 302
        data_api_client.create_work_order.assert_called_with(
            briefId=1234,
            supplierCode=4321,
            workOrder={
                'orderPeriod': u'6 months',
                'seller': {
                    'contact': u'joe bloggs',
                    'name': u'test supplier',
                    'abn': u'123456'
                },
                'deliverables': u'test summary',
                'son': 'SON3364729',
                'additionalTerms': 'some terms',
                'securityClearance': 'I have clearance'
            }
        )

    def test_create_new_work_order_invalid_form(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.find_brief_responses.return_value = {
            'briefResponses': [
                {
                    'supplierCode': 4321,
                    'supplierName': 'test supplier'
                }
            ]
        }

        res = self.client.post(
            self.expand_path(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
                '/work-orders/create'
            ),
            data={
                'seller': 9999,
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 400

    def test_create_new_work_order_api_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.find_brief_responses.return_value = {
            'briefResponses': [
                {
                    'supplierCode': 4321,
                    'supplierName': 'test supplier'
                }
            ]
        }

        data_api_client.create_work_order.side_effect = APIError(mock.Mock(status_code=500))

        res = self.client.post(
            self.expand_path(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
                '/work-orders/create'
            ),
            data={
                'seller': 4321,
                'csrf_token': FakeCsrf.valid_token,
            })

        text = res.get_data(as_text=True)
        assert res.status_code == 500
        assert 'Request failed' in text


@mock.patch('app.buyers.views.work_orders.data_api_client')
class TestViewWorkOrder(BaseApplicationTest):
    def test_view_work_order(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = test_brief
            data_api_client.get_work_order.return_value = test_work_order

            res = self.client.get(self.expand_path('/work-orders/1234'))
            assert res.status_code == 200

    def test_404_if_work_order_not_found(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_work_order.side_effect = APIError(mock.Mock(status_code=404))

            res = self.client.get(self.expand_path(
                '/work-orders/1234')
            )

            assert res.status_code == 404

    def test_404_if_work_order_not_allowed_access(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer(user_id=1)
            data_api_client.get_work_order.return_value = test_work_order
            data_api_client.get_brief.return_value = test_brief

            res = self.client.get(self.expand_path(
                '/work-orders/1234')
            )

            assert res.status_code == 404

    def test_work_order_pdf(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_work_order.return_value = test_work_order
        data_api_client.get_brief.return_value = test_brief
        res = self.client.get(self.expand_path('/work-orders/workorder_1234.pdf'))
        assert 200 == res.status_code
        assert res.mimetype == 'application/pdf'

    def test_work_order_pdf_unauthorised(self, data_api_client):
        self.login_as_buyer(user_id=1)
        data_api_client.get_work_order.return_value = test_work_order
        data_api_client.get_brief.return_value = test_brief
        res = self.client.get(self.expand_path('/work-orders/workorder_1234.pdf'))
        assert 404 == res.status_code
        assert res.mimetype != 'application/pdf'


@mock.patch('app.buyers.views.work_orders.data_api_client')
class TestEditWorkOrderQuestion(BaseApplicationTest):
    def test_view_work_order_question(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = test_brief
            data_api_client.get_work_order.return_value = test_work_order

            res = self.client.get(self.expand_path('/work-orders/1234/questions/number'))
            assert res.status_code == 200

    def test_404_if_work_order_question_not_authorised(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer(user_id=1)
            data_api_client.get_brief.return_value = test_brief
            data_api_client.get_work_order.return_value = test_work_order

            res = self.client.get(self.expand_path('/work-orders/1234/questions/number'))

            assert res.status_code == 404

    def test_404_if_work_order_question_not_found(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = test_brief
            data_api_client.get_work_order.return_value = test_work_order

            res = self.client.get(self.expand_path(
                '/work-orders/1234/questions/blah')
            )

            assert res.status_code == 404

    def test_update_work_order_question(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.get_work_order.return_value = test_work_order

        res = self.client.post(
            self.expand_path('/work-orders/1234/questions/number'),
            data={
                'number': 4321,
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 302
        data_api_client.update_work_order.assert_called_with(1234, {'number': '4321'})

    def test_404_if_update_work_order_question_not_authorised(self, data_api_client):
        self.login_as_buyer(user_id=1)
        data_api_client.get_brief.return_value = test_brief
        data_api_client.get_work_order.return_value = test_work_order

        res = self.client.post(
            self.expand_path('/work-orders/1234/questions/number'),
            data={
                'number': 4321,
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 404
        data_api_client.update_work_order.assert_not_called

    def test_update_work_order_address_question(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.get_work_order.return_value = test_work_order

        res = self.client.post(
            self.expand_path('/work-orders/1234/questions/agency'),
            data={
                'abn': 'test abn',
                'contact': 'test contact',
                'name': 'test name',
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 302
        data_api_client.update_work_order.assert_called_with(
            1234,
            {'agency': {
                'abn': 'test abn',
                'contact': 'test contact',
                'name': 'test name'}}
        )

    def test_update_new_work_order_question_invalid_form(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = test_brief
        data_api_client.get_work_order.return_value = test_work_order

        res = self.client.post(
            self.expand_path('/work-orders/1234/questions/number'),
            data={
                'number': '',
                'csrf_token': FakeCsrf.valid_token,
            })

        assert res.status_code == 400
