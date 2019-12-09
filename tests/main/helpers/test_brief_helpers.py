from app.main.helpers.brief_helpers import (
    count_brief_responses_by_size_and_status,
    format_winning_supplier_size
)
from ...helpers import BaseApplicationTest


class TestBriefHelpers(BaseApplicationTest):
    def test_count_brief_responses_by_size_and_status(self):
        brief_responses = self._get_dos_brief_responses_fixture_data()["briefResponses"]
        expected_result = {
            "incomplete_sme_responses": 3,
            "incomplete_large_responses": 0,
            "incomplete_responses_total": 3,
            "completed_sme_responses": 4,
            "completed_large_responses": 1,
            "completed_responses_total": 5
        }
        assert count_brief_responses_by_size_and_status(brief_responses) == expected_result

    def test_format_winning_supplier_size(self):
        assert format_winning_supplier_size("micro") == "SME"
        assert format_winning_supplier_size("small") == "SME"
        assert format_winning_supplier_size("medium") == "SME"
        assert format_winning_supplier_size("large") == "large"
