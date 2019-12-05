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


# TODO: split the manifest sections and add the relevant description for each DOS5 lot to dm-frameworks instead
def get_evaluation_description(brief, brief_content):
    # For DOS4 briefs only, add in mandatory evaluation method. This is missing from the DOS4 display_brief manifest
    # summary_page_description.
    #   Digital Specialists: work history
    #   Digital Outcomes / User Research Participants: written proposal
    if brief['frameworkSlug'] == 'digital-outcomes-and-specialists-4':
        for section in brief_content.summary(brief):
            if section.name == 'How suppliers will be evaluated':
                if brief['lotSlug'] == 'digital-specialists':
                    return 'All suppliers will be asked to provide a work history.'
                return 'All suppliers will be asked to provide a written proposal.'
    return None
