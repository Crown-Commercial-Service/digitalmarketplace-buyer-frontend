## Rendering a React component in Python

### `render_component`

Generate the markup for a React component for server-side rendering. Currently only available inside a python view

#### Arguments

1. `path`: Relative path to component from `static/src`.
2. `props`: Initial state/props for component
3. `to_static_markup`: Whether to return plain markup or React bound markup
4. `request_headers`: Headers to send to node service on render request

#### Returns

`Object`: With either a key for resulting `markup` or a key for `errors`

#### Examples

Rendering basic component:
```python
render_component('App.js', { 'foo': 'bar' })
```

### Caveats

There must be a node rendering service running.

You can define where this service lives in `config.py`

The two properties are:

1. `REACT_RENDER_URL`: `String`, The endpoint where the rendering service lives
2. `REACT_RENDER`: `Boolean`, Whether to call the service or not. Useful in debugging / testing mode.


Example:
```
REACT_RENDER_URL = 'http://127.0.0.1:63578/render'
REACT_RENDER = not DEBUG
```
