def get_template_data(blueprint, view_data):
    """Returns a single object holding the base template data with the view
       data added"""

    template_data = blueprint.config['BASE_TEMPLATE_DATA']
    for key in view_data:
        template_data[key] = view_data[key]
    return template_data


def get_keywords_from_request(request):
    if request.args['q']:
        return request.args['q']
    else:
        return ""
