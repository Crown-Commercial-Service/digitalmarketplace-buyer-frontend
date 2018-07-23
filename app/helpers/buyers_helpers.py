from flask import abort
from flask_login import current_user


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


def is_brief_correct(brief, framework_slug, lot_slug, current_user_id):
    return brief['frameworkSlug'] == framework_slug \
        and brief['lotSlug'] == lot_slug \
        and is_brief_associated_with_user(brief, current_user_id) \
        and not brief_is_withdrawn(brief)


def is_brief_associated_with_user(brief, current_user_id):
    if current_user and current_user.role == 'admin':
        return True
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


def counts_for_failed_and_eligible_brief_responses(brief_id, data_api_client):
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
    return all(brief_response['essentialRequirements'])


def get_sorted_responses_for_brief(brief, data_api_client):
    brief_responses = data_api_client.find_brief_responses(brief['id'])['briefResponses']
    return brief_responses


def allowed_email_domain(current_user_id, brief, data_api_client=None):
    if not all([current_user_id, brief, data_api_client]):
        return False
    if not brief.get('users') or brief.get('users')[0] is None:
        return False
    current_user = data_api_client.get_user(current_user_id).get('users')
    email_domain = current_user.get('email_address').split('@')[-1]
    brief_user_email = brief.get('users')[0].get('emailAddress').split('@')[-1]
    return email_domain == brief_user_email


def remove_non_cascade_fields(brief, section, current_question_id, update_data=None):
    if not brief.get('lot') == 'training':
        return

    all_lds = {
        'Digital foundations': 'ldsDigitalFoundation',
        'Agile delivery': 'ldsAgileDelivery',
        'User research': 'ldsUserResearch',
        'Content design': 'ldsContentDesign',
        'Other': 'trainingDetail'
    }

    to_remove = []
    if (current_question_id == 'description-of-training' or
            current_question_id == 'whatTraining'):
        for k, v in all_lds.iteritems():
            if update_data:
                what_training = update_data.get('whatTraining', [])
                if what_training and k not in what_training:
                    to_remove.append(v)
            elif k not in brief.get('whatTraining', []):
                to_remove.append(v)

            update_cascaded_optional_fields(brief, section, v)

    if current_question_id in all_lds.itervalues():
        to_remove = []
        for k, v in all_lds.iteritems():
            if k not in brief.get('whatTraining', []):
                to_remove.append(v)

            update_cascaded_optional_fields(brief, section, v)

    for tr in to_remove:
        if any(q for q in section.questions if q.id == tr):
            section.questions.remove(
                next(q for q in section.questions if q.id == tr))


def update_cascaded_optional_fields(brief, section, current_question_id):
    lds_sub_fields = {
        'ldsDigitalFoundation': [
            'ldsDigitalFoundationProposalOrLds',
            'ldsDigitalFoundationUnits',
            'ldsDigitalFoundationTrainingNeeds'
        ],
        'ldsAgileDelivery': [
            'ldsAgileDeliveryProposalOrLds',
            'ldsAgileDeliveryUnits',
            'ldsAgileDeliveryTrainingNeeds'
        ],
        'ldsUserResearch': [
            'ldsUserResearchProposalOrLds',
            'ldsUserResearchUnits',
            'ldsUserResearchTrainingNeeds'
        ],
        'ldsContentDesign': [
            'ldsContentDesignProposalOrLds',
            'ldsContentDesignUnits',
            'ldsContentDesignTrainingNeeds'
        ],
        'trainingDetail': [
            'trainingDetailType',
            'trainingDetailCover'
        ]
    }
    field_names = []
    lds_field = lds_sub_fields.get(current_question_id)
    if current_question_id == 'trainingDetail':
        field_names = lds_field
    elif lds_field:
        radio_name = lds_field[0]
        radio_value = brief.get(radio_name, None)

        if not radio_value:
            field_names.append(radio_name)
        elif radio_value == 'ldsUnits':
            field_names.append(lds_field[1])
        elif radio_value == 'specify':
            field_names.append(lds_field[2])

    for field_name in field_names:
        field = section.get_question(field_name)
        if field is not None:  # the question might be removed earlier
            field.optional = False
