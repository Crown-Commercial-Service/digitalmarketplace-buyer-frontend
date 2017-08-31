from flask import redirect
from .. import main


# Any invites sent before the new user-frontend becomes active will be linking to this route. We need to maintain it
# for seven days after the user-frontend goes live.
@main.route('/create-user/<string:encoded_token>', methods=['GET'])
def create_user(encoded_token):
    return redirect('/user/create/{}'.format(encoded_token), 301)
