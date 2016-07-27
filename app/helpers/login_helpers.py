from flask_login import current_user
from flask import redirect, url_for


def redirect_logged_in_user(next_url=None):
    if current_user.is_authenticated():
        if current_user.role == 'supplier':
            if next_url and next_url.startswith('/suppliers'):
                return redirect(next_url)
            else:
                return redirect('/suppliers')
        if current_user.role.startswith('admin'):
            if next_url and next_url.startswith('/admin'):
                return redirect(next_url)
            else:
                return redirect('/admin')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        else:
            return redirect(url_for('.supplier_search'))

    return redirect(url_for('.index'))
