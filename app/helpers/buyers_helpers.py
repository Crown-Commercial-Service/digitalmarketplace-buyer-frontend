from flask import abort

from ..buyers import content_loader


def get_framework_and_lot(framework_slug, lot_slug, data_api_client, status=None, must_allow_brief=False):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)

    if status and framework['status'] != status:
        abort(404)
    if must_allow_brief and not lot['allowsBrief']:
        abort(404)

    return framework, lot


def count_suppliers_on_lot(framework, lot):

    # TODO: Implement this properly!

    return 987


def is_brief_associated_with_user(brief, current_user_id):
    user_ids = [user.get('id') for user in brief.get('users', [])]
    return current_user_id in user_ids


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


def add_response_counts_to_briefs(briefs, data_api_client):
    for brief in briefs:
        responses = data_api_client.find_brief_responses(brief_id=brief['id'])
        brief['responses_count'] = len(responses)

    return briefs


def clarification_questions_open(brief):
    # TODO: Implement this properly
    return True


def classify_and_count_brief_responses(brief_id, data_api_client):
    brief_responses = data_api_client.find_brief_responses(brief_id)['briefResponses']
    failed_count = 0
    eligible_count = 0
    for brief_response in brief_responses:
        if all_essentials_are_true(brief_response):
            eligible_count += 1
        else:
            failed_count += 1
    return failed_count, eligible_count


def all_essentials_are_true(brief_response):
    return len([essential for essential in brief_response['essentialRequirements'] if essential is False]) == 0
