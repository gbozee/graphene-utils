import json

from urllib.parse import urlencode


def url_string(string="/graphql", **url_params):
    if url_params:
        string += "?" + urlencode(url_params)
    return string


def response_json(response):
    return json.loads(response.content.decode())


j = lambda **kwargs: json.dumps(kwargs)
jl = lambda **kwargs: json.dumps([kwargs])


class MockResponse(object):
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        pass
