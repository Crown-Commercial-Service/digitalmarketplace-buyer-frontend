try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def parse_links(links):
    pagination_links = {
        "prev": None,
        "next": None
    }

    if 'prev' in links:
        pagination_links['prev'] = parse_qs(urlparse(links['prev']).query)
    if 'next' in links:
        pagination_links['next'] = parse_qs(urlparse(links['next']).query)

    return pagination_links


def process_page(page):
    try:
        int(page)
        return page
    except ValueError:
        return "1"  # default


def get_label_for_lot_param(lot_param):
    lots = {
        'saas': u'Software as a Service',
        'paas': u'Platform as a Service',
        'iaas': u'Infrastructure as a Service',
        'scs': u'Specialist Cloud Services',
        'all': u'All categories'
    }
    if lot_param in lots:
        return lots[lot_param]


def get_one_framework_by_status_in_order_of_preference(frameworks, statuses_in_order_of_preference):
    for status in statuses_in_order_of_preference:
        for framework in frameworks:
            if framework.get('status') == status:
                return framework
