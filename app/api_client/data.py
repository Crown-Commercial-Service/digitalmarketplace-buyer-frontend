from __future__ import unicode_literals
from .base import BaseAPIClient


class DataAPIClient(BaseAPIClient):

    # Suppliers
    def find_suppliers(self, data=None):
        return self._get(
            "/suppliers/search",
            data=data
        )

    def get_supplier(self, supplier_id):
        return self._get(
            "/suppliers/{}".format(supplier_id)
        )
