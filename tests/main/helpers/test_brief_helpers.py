import pytest
import mock
from app.main.helpers.brief_helpers import (
    count_brief_responses_by_size_and_status,
    format_winning_supplier_size,
    show_mandatory_assessment_method
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

    @pytest.mark.parametrize('status', ['draft', 'closed', 'awarded', 'cancelled', 'unsuccessful'])
    def test_show_mandatory_assessment_method_for_non_live_briefs(self, status):
        brief = {
            'status': status,
            'publishedAt': '2019-11-01'
        }
        current_app = mock.Mock()
        assert show_mandatory_assessment_method(brief, current_app)

    def test_do_not_show_mandatory_assessment_method_for_live_briefs_before_date(self):
        brief = {
            'status': 'live',
            'publishedAt': '2019-11-01'
        }
        current_app = mock.Mock()
        current_app.config = {'SHOW_BRIEF_MANDATORY_EVALUATION_METHOD': '2019-11-02'}
        assert not show_mandatory_assessment_method(brief, current_app)

    @pytest.mark.parametrize('date', ['2019-11-02', '2019-11-03'])
    def test_show_mandatory_assessment_method_for_live_briefs_on_or_after_date(self, date):
        brief = {
            'status': 'live',
            'publishedAt': date
        }
        current_app = mock.Mock()
        current_app.config = {'SHOW_BRIEF_MANDATORY_EVALUATION_METHOD': '2019-11-02'}
        assert show_mandatory_assessment_method(brief, current_app)
