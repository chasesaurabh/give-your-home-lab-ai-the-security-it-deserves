"""Small strict JSON and loopback-only transport helpers."""
import json
import math
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
    def finite_float(value):
        # Valid JSON numeric syntax can still overflow a Python float.
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("JSON number exceeds finite float range")
        return parsed
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=reject_constant, parse_float=finite_float)


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
