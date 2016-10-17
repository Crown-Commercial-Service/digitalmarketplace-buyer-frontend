import json
import hashlib
import requests
from flask import current_app
from flask.json import JSONEncoder
from flask import request

from .exceptions import ReactRenderingError, RenderServerError


class RenderedComponent(object):
    def __init__(self, markup, props, slug):
        self.markup = markup
        self.props = props
        self.slug = slug

    def __str__(self):
        return self.markup

    def __unicode__(self):
        return unicode(self.markup)

    def get_bundle(self):
        bundle_url = current_app.config.get('REACT_BUNDLE_URL', '/')
        return bundle_url + self.slug + '.js'

    def get_vendor_bundle(self):
        bundle_url = current_app.config.get('REACT_BUNDLE_URL', '/')
        return bundle_url + 'vendor.js'

    def get_slug(self):
        return self.slug

    def get_props(self):
        return self.props

    def render(self):
        return str(self.markup)


class RenderServer(object):
    def render(self, path, props=None, to_static_markup=False, request_headers=None):
        url = current_app.config.get('REACT_RENDER_URL', '')

        if props is None:
            props = {}

        api_url = current_app.config.get('DM_DATA_API_URL', None)
        # Pass current route path for React router to use
        props.update({
            '_serverContext': {
                'location': request.path,
                'api_url': api_url
            }
        })

        serialized_props = json.dumps(props, cls=JSONEncoder)

        if not current_app.config.get('REACT_RENDER', ''):
            return RenderedComponent('', serialized_props)

        options = {
            'path': path,
            'serializedProps': serialized_props,
            'toStaticMarkup': to_static_markup
        }
        serialized_options = json.dumps(options)
        options_hash = hashlib.sha1(serialized_options.encode('utf-8')).hexdigest()

        all_request_headers = {'content-type': 'application/json'}

        # Add additional requests headers if the requet_headers dictionary is specified
        if request_headers is not None:
            all_request_headers.update(request_headers)

        try:
            res = requests.post(
                url,
                data=serialized_options,
                headers=all_request_headers,
                params={'hash': options_hash}
            )
        except requests.ConnectionError:
            raise RenderServerError('Could not connect to render server at {}'.format(url))

        if res.status_code != 200:
            raise RenderServerError(
                'Unexpected response from render server at {} - {}: {}'.format(url, res.status_code, res.text)
            )

        obj = res.json()

        markup = obj.get('markup', None)
        err = obj.get('error', None)
        slug = obj.get('slug', 'main')

        if err:
            if 'message' in err and 'stack' in err:
                raise ReactRenderingError(
                    'Message: {}\n\nStack trace: {}'.format(err['message'], err['stack'])
                )
            raise ReactRenderingError(err)

        if markup is None:
            raise ReactRenderingError('Render server failed to return markup. Returned: {}'.format(obj))

        return RenderedComponent(markup, serialized_props, slug)


render_server = RenderServer()
