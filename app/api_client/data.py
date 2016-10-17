from __future__ import unicode_literals
from .base import BaseAPIClient


class DataAPIClient(BaseAPIClient):
    # Suppliers
    def find_suppliers(self, data=None, params=None):
        return self._get(
            "/suppliers/search",
            data=data, params=params
        )

    def get_supplier(self, supplier_code):
        return self._get(
            "/suppliers/{}".format(supplier_code)
        )

    def get_case_study(self, case_study_id):
        return self._get(
            "/case-studies/{}".format(case_study_id)
        )

    def get_roles(self, data=None, params=None):
        return self._get(
            "/roles",
            data=data, params=params
        )
