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


def chunk_string(string, chunk_length):
    return (string[0+i:chunk_length+i] for i in range(0, len(string), chunk_length))
