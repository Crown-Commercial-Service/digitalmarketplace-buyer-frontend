from flask_login import current_user


def user_context():
    """
    Makes user data available throughout the template with variable current_user
    example- {% if current_user.is_authenticated() %} {{ current_user.email_address }} {% endif %}
    """
    return {'current_user': current_user}
