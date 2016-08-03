from flask_login import current_user
from flask import current_app, redirect, render_template, Response, url_for


def redirect_logged_in_user(next_url=None):
    site_url_prefix = current_app.config['URL_PREFIX']
    if current_user.is_authenticated:
        if next_url and next_url.startswith(site_url_prefix):
            return redirect(next_url)
        else:
            return redirect(url_for('.supplier_search'))

    return redirect(url_for('.index'))


def render_template_with_csrf(template_name, status_code=200, **kwargs):
    response = Response(render_template(template_name, **kwargs))

    # CSRF tokens are user-specific, even if the user isn't logged in
    response.cache_control.private = True

    max_age = current_app.config['DM_DEFAULT_CACHE_MAX_AGE']
    max_age = min(max_age, current_app.config.get('CSRF_TIME_LIMIT', max_age))
    response.cache_control.max_age = max_age

    return response, status_code
