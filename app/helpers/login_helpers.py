from flask_login import current_user
from flask import current_app, redirect, url_for


def redirect_logged_in_user(next_url=None):
    site_url_prefix = current_app.config['URL_PREFIX']
    if current_user.is_authenticated:
        if next_url and next_url.startswith(site_url_prefix):
            return redirect(next_url)
        else:
            return redirect(url_for('.supplier_search'))

    return redirect(url_for('.index'))
