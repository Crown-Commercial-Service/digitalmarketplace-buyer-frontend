import mock
import app.helpers as helpers
from dmutils.content_loader import ContentLoader

from dmapiclient import api_stubs

content_loader = ContentLoader('tests/fixtures/content')
content_loader.load_manifest('dos', 'data', 'edit_brief')
questions_builder = content_loader.get_builder('dos', 'edit_brief')


def test_get_framework_and_lot():
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


def test_is_brief_associated_with_user():
    brief = api_stubs.brief(user_id=123)['briefs']
    assert helpers.buyers_helpers.is_brief_associated_with_user(brief, 123) is True
    assert helpers.buyers_helpers.is_brief_associated_with_user(brief, 234) is False


def test_brief_can_be_edited():
    assert helpers.buyers_helpers.brief_can_be_edited(api_stubs.brief(status='draft')['briefs']) is True
    assert helpers.buyers_helpers.brief_can_be_edited(api_stubs.brief(status='live')['briefs']) is False


def test_count_unanswered_questions():
    brief = {
        'status': 'draft',
        'frameworkSlug': 'dos',
        'lotSlug': 'digital-specialists',
        'required1': True,
        }
    content = content_loader.get_manifest('dos', 'edit_brief').filter(
        {'lot': 'digital-specialists'}
    )
    sections = content.summary(brief)

    unanswered_required, unanswered_optional = helpers.buyers_helpers.count_unanswered_questions(sections)
    assert unanswered_required == 1
    assert unanswered_optional == 2


def test_add_unanswered_counts_to_briefs():
    briefs = [{
        'status': 'draft',
        'frameworkSlug': 'dos',
        'lotSlug': 'digital-specialists',
        'required1': True,
    }]

    helpers.buyers_helpers.content_loader = content_loader

    assert helpers.buyers_helpers.add_unanswered_counts_to_briefs(briefs) == [{
        'status': 'draft',
        'frameworkSlug': 'dos',
        'lotSlug': 'digital-specialists',
        'required1': True,
        'unanswered_required': 1,
        'unanswered_optional': 2
    }
    ]
