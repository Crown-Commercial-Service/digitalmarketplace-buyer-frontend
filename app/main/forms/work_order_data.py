from collections import OrderedDict

questions = OrderedDict([(
    'number', {
        'description': 'Work Order number',
        'infoToAdd': 'Add a work order number',
        'heading': 'Work Order number',
        'summary': 'Add a work order number.',
        'label': 'Work Order number',
        'message': 'You must provide a Work Order number',
        'type': 'text',
    }), (
    'son', {
        'description': 'SON',
        'infoToAdd': 'Add an SON',
        'heading': 'SON',
        'summary': 'This is the SON',
        'label': 'SON',
        'message': 'You must provide an SON',
        'type': 'text',
    }), (
    'costCode', {
        'description': 'Buyer cost code',
        'infoToAdd': 'Add a buyer cost code (optional)',
        'heading': 'Buyer cost code',
        'summary': 'Add a buyer cost code.',
        'label': 'Buyer cost code (optional)',
        'message': 'You must provide a buyer cost code',
        'type': 'text',
    }), (
    'glCode', {
        'description': 'GL code',
        'infoToAdd': 'Add GL code (optional)',
        'heading': 'GL code',
        'summary': 'Add GL code.',
        'label': 'GL code (optional)',
        'message': 'You must provide a GL code',
        'type': 'text',
    }), (
    'agency', {
        'description': 'Buyer',
        'infoToAdd': 'Add buyer details',
        'heading': 'Buyer (Agency)',
        'summary': 'Add your name, the name of your Agency and the Agency\'s ABN.',
        'contactLabel': 'Agency representative',
        'contactMessage': 'You need to add your name',
        'nameLabel': 'Agency name',
        'nameMessage': 'You need to add the name of your Agency',
        'abnLabel': 'Agency ABN',
        'abnMessage': 'You need to add the ABN of your Agency',
        'type': 'address'
    }), (
    'seller', {
        'description': 'Seller',
        'infoToAdd': 'Add company',
        'heading': 'Seller',
        'summary': 'Company summary',
        'abnLabel': 'ABN',
        'abnMessage': 'You must provide an ABN',
        'nameLabel': 'Company name',
        'nameMessage': 'You must provide a company name',
        'contactLabel': 'Company Representative',
        'contactMessage': 'You must provide a company representative',
        'type': 'address'
    }), (
    'orderPeriod', {
        'description': 'Timeline',
        'infoToAdd': 'Add start date, end date or duration and extension options',
        'heading': 'Timeline',
        'summary': 'Add the start date, end date and any extension options. '
                   'For example \'3 months at a time, notified by email\'.',
        'label': 'Order period and extension options',
        'message': 'You must provide an order period',
    }), (
    'services', {
        'description': 'Services',
        'infoToAdd': 'Add services',
        'heading': 'Services',
        'summary': 'Add the services and deliverables to be provided by the seller.',
        'label': 'Services',
        'message': 'You need to add the services the seller will provide'
    }), (
    'deliverables', {
        'description': 'Deliverables',
        'infoToAdd': 'Add deliverables (optional)',
        'heading': 'Deliverables',
        'summary': 'Add any artifacts or outcomes that will be created as part of this order.',
        'label': 'Add deliverables (optional)',
        'message': 'You must provide deliverables'
    }), (
    'performanceCriteria', {
        'description': 'Performance criteria',
        'infoToAdd': 'Add performance criteria (optional)',
        'heading': 'Performance criteria',
        'summary': 'How will you judge the timeliness, quality and other attributes of the services '
                   'or deliverables? Are you applying the Digital Service Standard? If so, add that information here.',
        'label': 'Performance criteria (optional)',
        'message': 'You need to add the performance criteria'
    }), (
    'governance', {
        'description': 'Governance',
        'infoToAdd': 'Add governance details (optional)',
        'heading': 'Governance',
        'summary': 'Add any governance requirements such as regular meetings, reports or training.',
        'label': 'Governance (optional)',
        'message': 'You need to add governance details'
    }), (
    'personnel', {
        'description': 'Specified personnel',
        'infoToAdd': 'Add specified personnel (optional)',
        'heading': 'Specified personnel',
        'summary': 'Add the full names of all people who will do the work and specify if any are subcontractors. '
                   'For example, \'Matt Jones (Subcontractor)\'.',
        'label': 'Name or names (optional)',
        'message': 'You need to add names of all personnel'
    }), (
    'securityClearance', {
        'description': 'Security requirements',
        'infoToAdd': 'Add security requirements (optional)',
        'heading': 'Security requirements',
        'summary': 'Only request security clearance if access to classified material, '
                   'environments or assets is required.',
        'label': 'Security requirements (optional)',
        'message': 'You must provide security requirements'
    }), (
    'pricing', {
        'description': 'Pricing',
        'infoToAdd': 'Add the billable items',
        'heading': 'Pricing',
        'summary': 'Add the unit pricing. Each item should have a separate field. '
                   'For example, Senior Developer at $1200 for a 6 month contract (capped at $149,500). '
                   'Use a new line for each additional cost item.',
        'label': 'Description and cost (excl. GST)',
        'message': 'You need to add pricing information'
    }), (
    'paymentMilestones', {
        'description': 'Payment milestones',
        'infoToAdd': 'Add payment milestones (optional)',
        'heading': 'Payment milestones',
        'summary': 'Add payment milestones. For example 50% upfront, '
                   '25% on completion of concept design and 25% on acception into Live.',
        'label': 'Payment milestones (Optional)',
        'message': 'You need to add payment milestones'
    }), (
    'expenses', {
        'description': 'Expenses',
        'infoToAdd': 'Add expenses (optional)',
        'heading': 'Expenses',
        'summary': 'Add expenses description and costs.',
        'label': 'Description / Cost (excl. GST) (optional)',
        'message': 'You must provide expenses'
    }), (
    'agencyProperty', {
        'description': 'Buyer intellectual property',
        'infoToAdd': 'Add buyer intellectual property details (optional)',
        'heading': 'Buyer intellectual property',
        'summary': 'Add details of any intellectual property you will provide to the seller and conditions of use.',
        'label': 'Buyer intellectual property (optional)',
        'message': 'You must provide buyer intellectual property details'
    }), (
    'sellerProperty', {
        'description': 'Seller intellectual property',
        'infoToAdd': 'Add seller intellectual property details (optional)',
        'heading': 'Seller intellectual property',
        'summary': 'Add details of any intellectual property you will provide to the buyer and conditions of use.',
        'label': 'Seller\'s intellectual property (optional)',
        'message': 'You must provide seller intellectual property details'
    }), (
    'additionalTerms', {
        'description': 'Additional terms and conditions',
        'infoToAdd': 'Add additional requirements (optional)',
        'heading': 'Additional terms and conditions',
        'summary': 'Add any additional requirements consistent with the Deed. '
                   'For example, professional and public liability insurance.',
        'label': 'Additional terms and conditions (optional)',
        'message': 'You must provide additional requirements'
    }), (
    'additionalDocumentation', {
        'description': 'Additional documentation incorporated by reference',
        'infoToAdd': 'Add references to the additional documentation (optional)',
        'heading': 'Additional documentation incorporated by reference',
        'summary': 'Add the documention including dates version numbers or specify \'current at time of order\'. '
                   'Any documentation specified must be emailed to the other party.',
        'label': 'Additional documentation (optional)',
        'message': 'You must provide additional documentation'
    })
])
