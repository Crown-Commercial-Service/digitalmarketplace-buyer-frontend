# -*- coding: utf-8 -*-
from flask import abort, render_template 

from dmapiclient import HTTPError

from ...main import main

from app import data_api_client, content_loader
from app.helpers.search_helpers import get_template_data


@main.route('/digital-outcomes-and-specialists/opportunities/<brief_id>')
def get_brief_by_id(brief_id):
    template_data = get_template_data(main, {})
    temporary_message = {}

    try:
        briefs = data_api_client.get_brief(brief_id)
        brief = briefs.get('briefs')
        if brief == None or brief['status'] != 'live':
            abort(404, "Opportunity '{}' can not be found".format(brief_id)) 
    except HTTPError as e:
        if e.status == 404:
            abort(404, "Opportunity '{}' can not be found".format(brief_id)) 

    return render_template(
        'brief.html',
        brief=brief,
        **template_data
    )
