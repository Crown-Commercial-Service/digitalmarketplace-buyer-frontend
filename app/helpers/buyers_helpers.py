from flask import abort
from flask_login import current_user

from ..buyers import content_loader


def get_framework_and_lot(framework_slug, lot_slug, data_api_client):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)

    return framework, lot


def count_suppliers_on_lot(framework, lot):

    # TODO: Implement this properly!

    return 987


def is_brief_associated_with_user(brief):
    user_ids = [user.get('id') for user in brief.get('users')]
    return current_user.id in user_ids


def brief_can_be_edited(brief):
    return brief.get('status') == 'draft'


def count_unanswered_questions(brief_attributes):
    unanswered_required, unanswered_optional = (0, 0)
    for section in brief_attributes:
        for question in section.questions:
            if question.answer_required:
                unanswered_required += 1
            elif question.value in ['', [], None]:
                unanswered_optional += 1

    return unanswered_required, unanswered_optional


def add_unanswered_counts_to_briefs(briefs):
    for brief in briefs:
        content = content_loader.get_manifest(brief.get('frameworkSlug'), 'edit_brief').filter(
            {'lot': brief.get('lotSlug')}
        )
        sections = content.summary(brief)
        unanswered_required, unanswered_optional = count_unanswered_questions(sections)
        brief['unanswered_required'] = unanswered_required
        brief['unanswered_optional'] = unanswered_optional

    return briefs
