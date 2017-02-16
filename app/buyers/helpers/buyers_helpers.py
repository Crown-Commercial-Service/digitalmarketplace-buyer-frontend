from flask import abort
from datetime import datetime, timedelta


def get_framework_and_lot(framework_slug, lot_slug, data_api_client, status=None, must_allow_brief=False):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)

    if status and framework['status'] not in status:
        abort(404)
    if must_allow_brief and not lot['allowsBrief']:
        abort(404)

    return framework, lot


def is_brief_correct(brief, framework_slug, lot_slug, current_user_id):
    return (
        brief['frameworkSlug'] == framework_slug
        and brief['lotSlug'] == lot_slug
        and is_brief_associated_with_user(brief, current_user_id)
        and not brief_is_withdrawn(brief)
    )


def is_brief_associated_with_user(brief, current_user_id):
    user_ids = [user.get('id') for user in brief.get('users', [])]
    return current_user_id in user_ids


def brief_can_be_edited(brief):
    return brief.get('status') == 'draft'


def brief_is_withdrawn(brief):
    return brief.get('status') == 'withdrawn'


def section_has_at_least_one_required_question(section):
    required_questions = [q for q in section.questions if not q.get('optional')]
    return len(required_questions) > 0


def count_unanswered_questions(sections):
    unanswered_required, unanswered_optional = (0, 0)
    for section in sections:
        for question in section.questions:
            if question.answer_required:
                unanswered_required += 1
            elif question.value in ['', [], None]:
                unanswered_optional += 1

    return unanswered_required, unanswered_optional


def add_unanswered_counts_to_briefs(briefs, content_loader):
    for brief in briefs:
        content = content_loader.get_manifest(brief.get('frameworkSlug'), 'edit_brief').filter(
            {'lot': brief.get('lotSlug')}
        )
        sections = content.summary(brief)
        unanswered_required, unanswered_optional = count_unanswered_questions(sections)
        brief['unanswered_required'] = unanswered_required
        brief['unanswered_optional'] = unanswered_optional

    return briefs


def get_sorted_responses_for_brief(brief, data_api_client):
    brief_responses = data_api_client.find_brief_responses(brief['id'])['briefResponses']
    if brief.get("niceToHaveRequirements"):
        return sorted(
            brief_responses,
            key=lambda k: len([nice for nice in k['niceToHaveRequirements'] if nice is True]),
            reverse=True
        )
    else:
        return brief_responses
