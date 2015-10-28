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
