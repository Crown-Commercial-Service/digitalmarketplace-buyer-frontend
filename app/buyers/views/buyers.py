from ...buyers import buyers
from flask import render_template

from ...helpers.search_helpers import get_template_data


@buyers.route('/buyers')
def buyer_dashboard():
    template_data = get_template_data(buyers, {})
    return render_template(
        'buyers/dashboard.html',
        **template_data
    )
