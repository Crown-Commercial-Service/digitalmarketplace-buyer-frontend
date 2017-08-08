try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def parse_link(links, label):
    return parse_qs(urlparse(links[label]).query) if label in links else None


def get_one_framework_by_status_in_order_of_preference(frameworks, statuses_in_order_of_preference):
    for status in statuses_in_order_of_preference:
        for framework in frameworks:
            if framework.get('status') == status:
                return framework


def count_brief_responses_by_size(brief_responses, size):
    return len([response for response in brief_responses if response['supplierOrganisationSize'] in size])
