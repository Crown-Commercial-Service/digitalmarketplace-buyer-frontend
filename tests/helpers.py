from __future__ import absolute_import
import os
from app import create_app
import json


class BaseApplicationTest(object):
    def setup(self):
        self.app = create_app('test')
        self.client = self.app.test_client()

    @staticmethod
    def _get_fixture_data(fixture_filename):
        test_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".")
        )
        fixture_path = os.path.join(
            test_root, 'fixtures', fixture_filename
        )
        with open(fixture_path) as fixture_file:
            return json.load(fixture_file)

    @staticmethod
    def _get_search_results_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'search_results_fixture.json'
        )

    @staticmethod
    def _get_search_results_multiple_page_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'search_results_multiple_pages_fixture.json'
        )

    @staticmethod
    def _get_g4_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g4_service_fixture.json')

    @staticmethod
    def _get_g5_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g5_service_fixture.json')

    @staticmethod
    def _get_g6_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g6_service_fixture.json')

    @staticmethod
    def _get_supplier_fixture_data():
        return BaseApplicationTest._get_fixture_data('supplier_fixture.json')
