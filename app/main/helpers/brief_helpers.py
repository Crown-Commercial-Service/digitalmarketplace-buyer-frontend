SME, LARGE = ['micro', 'small', 'medium'], ['large']
COMPLETED_BRIEF_RESPONSE_STATUSES = ['submitted', 'pending-awarded', 'awarded']


def _count_brief_responses_by_size(brief_responses, size):
    return len([response for response in brief_responses if response['supplierOrganisationSize'] in size])


def count_brief_responses_by_size_and_status(brief_responses):
    counts = {}
    started_brief_responses = [response for response in brief_responses if response['status'] == 'draft']
    completed_brief_responses = [
        response for response in brief_responses if response['status'] in COMPLETED_BRIEF_RESPONSE_STATUSES
    ]
    counts["started_sme_responses"] = _count_brief_responses_by_size(started_brief_responses, SME)
    counts["started_large_responses"] = _count_brief_responses_by_size(started_brief_responses, LARGE)
    counts["started_responses_total"] = counts["started_sme_responses"] + counts["started_large_responses"]
    counts["completed_sme_responses"] = _count_brief_responses_by_size(completed_brief_responses, SME)
    counts["completed_large_responses"] = _count_brief_responses_by_size(completed_brief_responses, LARGE)
    counts["completed_responses_total"] = counts["completed_sme_responses"] + counts["completed_large_responses"]
    return counts


def format_winning_supplier_size(size):
    if size in SME:
        return "SME"
    elif size in LARGE:
        return "large"
