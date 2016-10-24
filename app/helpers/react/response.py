def from_response(request):
    result = {}
    for raw_key in request.form.keys():
        if raw_key not in ['csrf_token']:
            value = request.form.getlist(raw_key)
            key = raw_key.replace('[]', '')
            if len(value) == 1 and '[]' not in raw_key:
                result[key] = value[0]
            else:
                result[key] = value
    return result
