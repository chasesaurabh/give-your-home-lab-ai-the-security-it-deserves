"""Small strict JSON and loopback-only transport helpers."""
import json
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, HTTPRedirectHandler, build_opener


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("Non-finite JSON constant")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)


def local_endpoint(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path.rstrip("/") != "/v1" or parsed.port is None):
        raise ValueError("Use an explicitly authorized numeric-loopback http://host:port/v1 endpoint")
    return value.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused")


def local_opener():
    # Do not send fixture requests through inherited proxy configuration.
    return build_opener(ProxyHandler({}), NoRedirect())
