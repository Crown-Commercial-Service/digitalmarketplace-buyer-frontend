import os
from .exceptions import ComponentSourceFileNotFound
from .render_server import render_server


def render_component(path, props=None, to_static_markup=False, renderer=render_server, request_headers=None):
    return renderer.render(path, props, to_static_markup, request_headers)
