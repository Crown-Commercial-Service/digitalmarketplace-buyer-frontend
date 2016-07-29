import mock
import unittest
import datetime
from werkzeug.exceptions import NotFound

import app.helpers as helpers
from dmcontent.content_loader import ContentLoader

from dmapiclient import api_stubs

content_loader = ContentLoader('tests/fixtures/content')
content_loader.load_manifest('dos', 'data', 'edit_brief')
questions_builder = content_loader.get_builder('dos', 'edit_brief')


class TestBuyersHelpers(unittest.TestCase):
    def test_get_framework_and_lot(self):
        data_api_client = mock.Mock()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        framework, lot = helpers.buyers_helpers.get_framework_and_lot('digital-outcomes-and-specialists',
                                                                      'digital-specialists',
                                                                      data_api_client)

        assert framework['status'] == "live"
        assert framework['name'] == 'Digital Outcomes and Specialists'
        assert framework['slug'] == 'digital-outcomes-and-specialists'
        assert framework['clarificationQuestionsOpen'] is True
        assert lot == {'slug': 'digital-specialists',
                       'oneServiceLimit': False,
                       'allowsBrief': True,
                       'id': 1,
                       'name': 'Digital Specialists',
                       }

    def test_get_framework_and_lot_404s_for_wrong_framework_status(self):
        data_api_client = mock.Mock()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        self.assertRaises(NotFound, helpers.buyers_helpers.get_framework_and_lot, 'digital-outcomes-and-specialists',
                          'digital-specialists', data_api_client, {'status': 'live'})

    def test_get_framework_and_lot_404s_if_allows_brief_required(self):
        data_api_client = mock.Mock()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        self.assertRaises(NotFound, helpers.buyers_helpers.get_framework_and_lot, 'digital-outcomes-and-specialists',
                          'digital-specialists', data_api_client, {'must_allow_brief': True})

    def test_is_brief_correct(self):
        brief = api_stubs.brief(user_id=123, status='live')['briefs']

        assert helpers.buyers_helpers.is_brief_correct(
            brief, 'digital-outcomes-and-specialists', 'digital-specialists', 123
        ) is True

        assert helpers.buyers_helpers.is_brief_correct(
            brief, 'not-digital-outcomes-and-specialists', 'digital-specialists', 123
        ) is False

        assert helpers.buyers_helpers.is_brief_correct(
            brief, 'digital-outcomes-and-specialists', 'not-digital-specialists', 123
        ) is False

        assert helpers.buyers_helpers.is_brief_correct(
            brief, 'digital-outcomes-and-specialists', 'not-digital-specialists', 124
        ) is False

        assert helpers.buyers_helpers.is_brief_correct(
            api_stubs.brief(user_id=123, status='withdrawn')['briefs'],
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123
        ) is False

    def test_is_brief_associated_with_user(self):
        brief = api_stubs.brief(user_id=123)['briefs']
        assert helpers.buyers_helpers.is_brief_associated_with_user(brief, 123) is True
        assert helpers.buyers_helpers.is_brief_associated_with_user(brief, 234) is False

    def test_brief_can_be_edited(self):
        assert helpers.buyers_helpers.brief_can_be_edited(api_stubs.brief(status='draft')['briefs']) is True
        assert helpers.buyers_helpers.brief_can_be_edited(api_stubs.brief(status='live')['briefs']) is False

    def test_brief_is_withdrawn(self):
        assert helpers.buyers_helpers.brief_is_withdrawn(api_stubs.brief(status='withdrawn')['briefs']) is True
        assert helpers.buyers_helpers.brief_is_withdrawn(api_stubs.brief(status='live')['briefs']) is False

    def test_section_has_at_least_one_required_question(self):
        content = content_loader.get_manifest('dos', 'edit_brief').filter(
            {'lot': 'digital-specialists'}
        )

        sections_with_required_questions = {
            'section-1': True,
            'section-2': True,
            'section-4': False,
            'section-5': True
        }

        for section in content.sections:
            assert helpers.buyers_helpers.section_has_at_least_one_required_question(section) \
                == sections_with_required_questions[section.slug]

    def test_count_unanswered_questions(self):
        brief = {
            'status': 'draft',
            'frameworkSlug': 'dos',
            'lotSlug': 'digital-specialists',
            'required1': True
            }
        content = content_loader.get_manifest('dos', 'edit_brief').filter(
            {'lot': 'digital-specialists'}
        )
        sections = content.summary(brief)

        unanswered_required, unanswered_optional = helpers.buyers_helpers.count_unanswered_questions(sections)
        assert unanswered_required == 2
        assert unanswered_optional == 2

    def test_add_unanswered_counts_to_briefs(self):
        briefs = [{
            'status': 'draft',
            'frameworkSlug': 'dos',
            'lotSlug': 'digital-specialists',
            'required1': True
        }]

        assert helpers.buyers_helpers.add_unanswered_counts_to_briefs(briefs, content_loader) == [{
            'status': 'draft',
            'frameworkSlug': 'dos',
            'lotSlug': 'digital-specialists',
            'required1': True,
            'unanswered_required': 2,
            'unanswered_optional': 2
        }]

    def test_all_essentials_are_true(self):
        assert helpers.buyers_helpers.all_essentials_are_true(
            {"essentialRequirements": [True, True, True, True, True]}
        ) is True

        assert helpers.buyers_helpers.all_essentials_are_true(
            {"essentialRequirements": [True, True, False, True, True]}
        ) is False

        assert helpers.buyers_helpers.all_essentials_are_true(
            {"essentialRequirements": [False, False, False, False, False]}
        ) is False

        assert helpers.buyers_helpers.all_essentials_are_true(
            {"essentialRequirements": [True, True, True, True, False]}
        ) is False

    def test_counts_for_failed_and_eligible_brief_responses(self):
        data_api_client = mock.Mock()
        data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {"essentialRequirements": [True, True, True, True, True]},
                {"essentialRequirements": [True, False, True, True, True]},
                {"essentialRequirements": [True, True, False, False, True]},
                {"essentialRequirements": [True, True, True, True, True]},
                {"essentialRequirements": [True, True, True, True, False]},
            ]
        }

        assert helpers.buyers_helpers.counts_for_failed_and_eligible_brief_responses(1, data_api_client) == (3, 2)

    def test_get_sorted_responses_for_brief(self):
        data_api_client = mock.Mock()
        data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {"id": "five", "niceToHaveRequirements": [True, True, True, True, True]},
                {"id": "zero", "niceToHaveRequirements": [False, False, False, False, False]},
                {"id": "three", "niceToHaveRequirements": [True, True, False, False, True]},
                {"id": "five", "niceToHaveRequirements": [True, True, True, True, True]},
                {"id": "four", "niceToHaveRequirements": [True, True, True, True, False]},
                {"id": "one", "niceToHaveRequirements": [False, False, False, True, False]},
                {"id": "four", "niceToHaveRequirements": [True, True, True, True, False]},
            ]
        }
        brief = {"id": 1, "niceToHaveRequirements": ["Nice", "to", "have", "yes", "please"]}

        assert helpers.buyers_helpers.get_sorted_responses_for_brief(brief, data_api_client) == [
            {'id': 'five', 'niceToHaveRequirements': [True, True, True, True, True]},
            {'id': 'five', 'niceToHaveRequirements': [True, True, True, True, True]},
            {'id': 'four', 'niceToHaveRequirements': [True, True, True, True, False]},
            {'id': 'four', 'niceToHaveRequirements': [True, True, True, True, False]},
            {'id': 'three', 'niceToHaveRequirements': [True, True, False, False, True]},
            {"id": "one", "niceToHaveRequirements": [False, False, False, True, False]},
            {'id': 'zero', 'niceToHaveRequirements': [False, False, False, False, False]}
        ]

    def test_get_sorted_responses_does_not_sort_if_no_nice_to_haves(self):
        data_api_client = mock.Mock()
        data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {"id": "five"},
                {"id": "zero"},
                {"id": "three"},
                {"id": "five"}
            ]
        }
        brief = {"id": 1, "niceToHaveRequirements": []}
        assert helpers.buyers_helpers.get_sorted_responses_for_brief(brief, data_api_client) == [
            {"id": "five"},
            {"id": "zero"},
            {"id": "three"},
            {"id": "five"}
        ]
