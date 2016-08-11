# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmapiclient import api_stubs
import mock
from lxml import html
import pytest


@mock.patch('app.main.views.digital_outcomes_and_specialists.data_api_client')
class TestStartBriefInfoPage(BaseApplicationTest):
    def test_show_start_brief_info_page(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
                ))
            assert res.status_code == 200
            document = html.fromstring(res.get_data(as_text=True))
            assert document.xpath('//h1')[0].text_content().strip() == "Find an individual specialist"

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False)
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
                ))
            assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='open',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
                ))
            assert res.status_code == 404


@mock.patch('app.main.views.digital_outcomes_and_specialists.data_api_client')
class TestStartStudiosInfoPage(BaseApplicationTest):
    def test_show_start_studios_info_page(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='user-research-studios'),
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-studios"
                ))
            assert res.status_code == 200
            document = html.fromstring(res.get_data(as_text=True))
            assert document.xpath('//h1')[0].text_content().strip() == "Find a user research lab"

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='open',
                lots=[
                    api_stubs.lot(slug='user-research-studios'),
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-studios"
                ))
            assert res.status_code == 404
