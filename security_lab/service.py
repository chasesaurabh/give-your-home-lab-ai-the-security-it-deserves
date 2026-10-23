"""Owned loopback HTTP fixture. Educational only; never expose to a network."""
from collections import deque
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import socket
import threading

from .policy import RequestContext, hardened
from .protocol import strict_json
from .runner import load_fixture


class BenchServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = True

    def __init__(self, *, lifetime=2.0, workers=4, work_limit=8):
        super().__init__(("127.0.0.1", 0), BenchHandler)
        self.lifetime, self.work_limit = lifetime, work_limit
        self.capacity = threading.BoundedSemaphore(workers)
        self.guard = threading.Lock()
        self.documents = load_fixture("documents.json")
        # These are throwaway lab credentials, never examples to copy into a deployment.
        self.credentials = {secrets.token_urlsafe(32): RequestContext(True, "synthetic-alpha", "alpha"),
                            secrets.token_urlsafe(32): RequestContext(True, "synthetic-beta", "beta")}
        self.used = {}
        self.audit = deque(maxlen=64)

    def process_request(self, request, address):
        if not self.capacity.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.capacity.release()
            raise

    def process_request_thread(self, request, address):
        # Absolute connection lifetime: a byte-dribbling client cannot reset this clock.
        def expire():
            try:
                request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        deadline = threading.Timer(self.lifetime, expire)
        deadline.daemon = True
        deadline.start()
        try:
            super().process_request_thread(request, address)
        finally:
            deadline.cancel()
            self.capacity.release()

    def handle_error(self, request, client_address):
        # Fixture diagnostics avoid raw headers, addresses, tokens and tracebacks.
        with self.guard:
            self.audit.append({"event":"connection_error"})

    def consume(self, token):
        with self.guard:
            context = self.credentials.get(token)
            if context is None:
                return None, "unauthenticated"
            count = self.used.get(token, 0)
            if count >= self.work_limit:
                return None, "work_limit"
            self.used[token] = count + 1
            return context, "accepted"

    def revoke(self, token):
        with self.guard:
            self.credentials.pop(token, None)


class BenchHandler(BaseHTTPRequestHandler):
    server_version = "BenchFixture"

    def log_message(self, format, *args):
        pass

    def send_result(self, status, reason, **payload):
        raw = json.dumps({"reason":reason, **payload}).encode()
        with self.server.guard:
            self.server.audit.append({"request_id":secrets.token_hex(8), "status":status, "reason":reason})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def valid_transport(self):
        host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get_all("Host", []) != [host] or "Origin" in self.headers:
            self.send_result(403, "host_or_origin")
            return False
        return True

    def do_GET(self):
        if not self.valid_transport():
            return
        self.send_result(200 if self.path == "/health" else 404,
                         "fixture_running" if self.path == "/health" else "route")

    def do_POST(self):
        if not self.valid_transport():
            return
        if self.path != "/propose":
            return self.send_result(404, "route")
        auth = self.headers.get_all("Authorization", [])
        if len(auth) != 1 or not auth[0].startswith("Bearer ") or len(auth[0]) > 256:
            return self.send_result(401, "unauthenticated")
        # Scope is selected only by this server-owned credential map.
        context, reason = self.server.consume(auth[0][7:])
        if context is None:
            return self.send_result(429 if reason == "work_limit" else 401, reason)
        lengths = self.headers.get_all("Content-Length", [])
        if ("Transfer-Encoding" in self.headers or len(lengths) != 1
                or not lengths[0].isascii() or not lengths[0].isdecimal()):
            return self.send_result(400, "framing")
        length = int(lengths[0])
        if not 0 < length <= 4096:
            return self.send_result(413, "body_limit")
        if self.headers.get_all("Content-Type", []) != ["application/json"]:
            return self.send_result(415, "content_type")
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                return self.send_result(400, "incomplete_body")
            body = strict_json(raw)
        except (ValueError, UnicodeError, RecursionError):
            return self.send_result(400, "json")
        if type(body) is not dict or set(body) != {"proposal"}:
            return self.send_result(400, "request_schema")
        outcome = hardened(body["proposal"], context, 1, self.server.documents)
        self.send_result(200 if outcome.allowed else 403, outcome.reason,
                         allowed=outcome.allowed, result=outcome.payload)


@contextmanager
def owned_service(**options):
    server = BenchServer(**options)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval":0.02}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
