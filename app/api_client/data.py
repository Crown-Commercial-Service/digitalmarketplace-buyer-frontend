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

    def create_case_study(self, caseStudy={}):
        case_study_data = dict(caseStudy)

        return self._post(
            "/case-studies",
            data={"caseStudy": case_study_data},
        )

    def get_case_study(self, case_study_id):
        return self._get(
            "/case-studies/{}".format(case_study_id))

    def update_case_study(self, caseStudyId, caseStudy):
        return self._patch(
            "/case-studies/{}".format(caseStudyId),
            data={"caseStudy": caseStudy},
        )

    def get_roles(self, data=None, params=None):
        return self._get(
            "/roles",
            data=data, params=params
        )
