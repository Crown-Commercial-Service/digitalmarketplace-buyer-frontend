SME, LARGE = ['micro', 'small', 'medium'], ['large']
COMPLETED_BRIEF_RESPONSE_STATUSES = ['submitted', 'pending-awarded', 'awarded']
ALL_BRIEF_RESPONSE_STATUSES = ['draft', 'submitted', 'pending-awarded', 'awarded']
PUBLISHED_BRIEF_STATUSES = ['live', 'withdrawn', 'closed', 'awarded', 'cancelled', 'unsuccessful']


def _count_brief_responses_by_size(brief_responses, size):
    return len([response for response in brief_responses if response['supplierOrganisationSize'] in size])


def count_brief_responses_by_size_and_status(brief_responses):
    counts = {}
    incomplete_brief_responses = [response for response in brief_responses if response['status'] == 'draft']
    completed_brief_responses = [
        response for response in brief_responses if response['status'] in COMPLETED_BRIEF_RESPONSE_STATUSES
    ]
    counts["incomplete_sme_responses"] = _count_brief_responses_by_size(incomplete_brief_responses, SME)
    counts["incomplete_large_responses"] = _count_brief_responses_by_size(incomplete_brief_responses, LARGE)
    counts["incomplete_responses_total"] = counts["incomplete_sme_responses"] + counts["incomplete_large_responses"]
    counts["completed_sme_responses"] = _count_brief_responses_by_size(completed_brief_responses, SME)
    counts["completed_large_responses"] = _count_brief_responses_by_size(completed_brief_responses, LARGE)
    counts["completed_responses_total"] = counts["completed_sme_responses"] + counts["completed_large_responses"]
    return counts


def format_winning_supplier_size(size):
    if size in SME:
        return "SME"
    elif size in LARGE:
        return "large"


def show_mandatory_assessment_method(brief, current_app):
    # To ensure suppliers see the same info while a brief is live, only show for closed briefs or
    # briefs published after the feature flag date.
    if brief['status'] != 'live':
        return True
    if current_app.config['SHOW_BRIEF_MANDATORY_EVALUATION_METHOD']:
        if brief['publishedAt'] >= current_app.config['SHOW_BRIEF_MANDATORY_EVALUATION_METHOD']:
            return True
    return False


# TODO: split the manifest sections and add the relevant description for each DOS5 lot instead
def get_evaluation_description(brief, current_app, brief_content):
    # Add in mandatory evaluation method, missing from the display_brief manifest summary_page_description
    #   Digital Specialists: work history
    #   Digital Outcomes / User Research Participants: written proposal
    if show_mandatory_assessment_method(brief, current_app):
        for section in brief_content.summary(brief):
            if section.name == 'How suppliers will be evaluated':
                if brief['lotSlug'] == 'digital-specialists':
                    return 'All suppliers will be asked to provide a work history.'
                return 'All suppliers will be asked to provide a written proposal.'
    return None
