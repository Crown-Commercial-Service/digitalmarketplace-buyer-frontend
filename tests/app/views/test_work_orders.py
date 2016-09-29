# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmutils.forms import FakeCsrf
from dmapiclient import api_stubs, HTTPError, APIError
from dmcontent.content_loader import ContentLoader
import mock
from lxml import html
import pytest


@mock.patch('app.buyers.views.work_orders.data_api_client')
class TestSelectSellerForWorkOrder(BaseApplicationTest):
    def test_start_work_order_page_renders(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_brief.return_value = api_stubs.brief()
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
        data_api_client.get_brief.return_value = api_stubs.brief()
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
                'orderPeriod': '',
                'securityClearance': '',
                'additionalTerms': '',
                'deliverables': '',
                'seller': {
                    'contact': 'joe bloggs',
                    'name': 'test supplier',
                    'abn': '123456'
                }
            }
        )

    def test_create_new_work_order_invalid_form(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_brief.return_value = api_stubs.brief()
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
        data_api_client.get_brief.return_value = api_stubs.brief()
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
            data_api_client.get_work_order.return_value = {
                'workOrder': {
                    'orderPeriod': '',
                    'securityClearance': '',
                    'additionalTerms': '',
                    'deliverables': '',
                    'seller': {
                        'contact': 'joe bloggs',
                        'name': 'test supplier',
                        'abn': '123456'
                    }
                }
            }

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
