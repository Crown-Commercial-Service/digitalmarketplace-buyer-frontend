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
