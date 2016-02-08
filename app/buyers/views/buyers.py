from flask import render_template
from flask_login import current_user

from app import data_api_client
from .. import buyers
from ...helpers.search_helpers import get_template_data


@buyers.route('/buyers')
def buyer_dashboard():
    template_data = get_template_data(buyers, {})
    user_briefs = data_api_client.find_briefs(current_user.id).get('briefs', [])
    draft_briefs = [brief for brief in user_briefs if brief['status'] == 'draft']
    live_briefs = [brief for brief in user_briefs if brief['status'] == 'live']

    return render_template(
        'buyers/dashboard.html',
        draft_briefs=draft_briefs,
        live_briefs=live_briefs,
        **template_data
    )
