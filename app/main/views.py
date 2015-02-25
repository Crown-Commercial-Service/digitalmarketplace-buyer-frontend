from . import main
from app import models
from flask import abort, render_template, request, jsonify, Response
from ..helpers.presenters import SearchResults

def get_template_data(blueprint, view_data):
    template_data = blueprint.config['BASE_TEMPLATE_DATA']
    for key in view_data:
        template_data[key] = view_data[key];
    return template_data

def get_filters_from_request(request):
    # TODO: only use request arguments that map to recognised filters
    filters = {}
    for key in request.args:
        if key != 'q':
            filters[key] = request.args[key]
    return filters

def get_keywords_from_request(request):
    if request.args['q']:
        return request.args['q']
    else:
        return ""

@main.route('/')
def index():
    return "Hello, World!", 200

@main.route('/service/<service_id>')
def get_service_by_id(service_id):
    try:
        service = models.get_service(service_id)
        return Response(service, mimetype='application/json')
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)


@main.route('/search')
def search():
    search_keywords = get_keywords_from_request(request)
    request_filters = get_filters_from_request(request)
    response = models.search_for_service(keywords=search_keywords, filters=request_filters)
    search_results_obj = SearchResults(response)
    template_data = get_template_data(main, {
        'title' : 'Search results',
        'search_keywords' : search_keywords,
        'filter_groups' : search_results_obj.get_filter_groups(blueprint=main, request_filters=request_filters),
        'services' : search_results_obj.get_results()['services']
    })
    return render_template('search.html', **template_data)

@main.route('/search/<query>/<lot>')
def search_with_lot(query, lot):
    response = models.search_with_lot_filter(query, lot)
    search_results_obj = SearchResults(response)
    template_data = get_template_data(main, {
        'title' : 'Search results',
        'filter_groups' : search_results_obj.get_filter_groups(main),
        'services' : search_results_obj.get_results()['services']
    })
    return render_template('search.html', **template_data)

@main.route('/search/<query>/filter')
def search_with_filters(query):
    response = models.search_with_filters(query, request.args)
    search_results_obj = SearchResults(response)
    template_data = get_template_data(main, {
        'title' : 'Search results',
        'filter_groups' : search_results_obj.get_filter_groups(main),
        'services' : search_results_obj.get_results()['services']
    })
    return render_template('search.html', **template_data)

