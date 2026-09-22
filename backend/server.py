"""HTTP adapter and static file server. Bind only to loopback for this local demo."""
import json
import mimetypes
import re
import sqlite3
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from .service import APIError

FRONTEND = Path(__file__).resolve().parent.parent / 'frontend'


def make_handler(workshop):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'IntakeDesk/1.0'

        def log_message(self, fmt, *args):
            # HTTP status only: avoid logging customer notes or request bodies.
            if len(args) > 1 and str(args[1]).startswith(('4', '5')):
                super().log_message(fmt, *args)

        def send(self, status, data, content_type='application/json; charset=utf-8'):
            body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'")
            self.end_headers()
            self.wfile.write(body)

        def body(self):
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise APIError(415, 'Use application/json.')
            try:
                size = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise APIError(400, 'Invalid content length.')
            if not 0 < size <= 32768:
                raise APIError(413, 'Request body must be between 1 and 32768 bytes.')
            try:
                data = json.loads(self.rfile.read(size))
            except (ValueError, UnicodeDecodeError):
                raise APIError(400, 'Invalid JSON.')
            if not isinstance(data, dict):
                raise APIError(400, 'JSON body must be an object.')
            return data

        def handle_request(self):
            try:
                # Local-only demo. No CORS, and no cross-origin mutations.
                host = urlparse('http://' + self.headers.get('Host', '')).hostname
                if host not in ('localhost', '127.0.0.1', '::1'):
                    raise APIError(403, 'This demo only accepts local requests.')
                if self.command != 'GET':
                    origin = self.headers.get('Origin')
                    if origin and urlparse(origin).netloc != self.headers.get('Host'):
                        raise APIError(403, 'Cross-origin writes are not supported.')
                path = urlparse(self.path).path
                if path == '/api/health' and self.command == 'GET':
                    return self.send(200, {'ok': True, 'application': 'Intake Desk'})
                if not path.startswith('/api/'):
                    if self.command != 'GET':
                        raise APIError(405, 'Method not allowed.')
                    relative = unquote(path).lstrip('/') or 'index.html'
                    file = (FRONTEND / relative).resolve()
                    if not file.is_relative_to(FRONTEND) or not file.is_file():
                        raise APIError(404, 'File not found.')
                    return self.send(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
                user = workshop.user(self.headers.get('X-Demo-User', 'alex'))
                if self.command == 'GET':
                    if path == '/api/bootstrap':
                        return self.send(200, workshop.bootstrap(user))
                    if path == '/api/requests':
                        return self.send(200, workshop.list_requests(user))
                    if path == '/api/dashboard':
                        return self.send(200, workshop.dashboard(user))
                    if path == '/api/outbox':
                        return self.send(200, workshop.outbox(user))
                    match = re.fullmatch(r'/api/requests/(\d+)', path)
                    if match:
                        return self.send(200, workshop.detail(user, int(match[1])))
                elif self.command in ('POST', 'PATCH'):
                    data = self.body()
                    if path == '/api/requests' and self.command == 'POST':
                        return self.send(201, workshop.create(user, data))
                    if path == '/api/imports/dropoff' and self.command == 'POST':
                        event_id = data.get('event_id')
                        if not event_id:
                            raise APIError(400, 'event_id is required for an import.')
                        result = workshop.create(user, data, event_id)
                        return self.send(200 if result['duplicate'] else 201, result)
                    if path == '/api/outbox/process' and self.command == 'POST':
                        return self.send(200, workshop.process_outbox(user, data.get('fail_first', False)))
                    match = re.fullmatch(r'/api/requests/(\d+)(?:/([a-z-]+))?', path)
                    if match:
                        request_id, action = int(match[1]), match[2]
                        if self.command == 'PATCH' and action is None:
                            return self.send(200, workshop.update(user, request_id, data))
                        if self.command == 'POST' and action:
                            return self.send(200, workshop.action(user, request_id, action, data))
                raise APIError(404, 'Endpoint not found.')
            except APIError as exc:
                self.send(exc.status, {'error': exc.message})
            except sqlite3.Error:
                self.send(500, {'error': 'Database operation failed. Restart the demo if this persists.'})
            except Exception:
                import traceback
                traceback.print_exc()
                self.send(500, {'error': 'Unexpected server error. Check the terminal for details.'})

        do_GET = handle_request
        do_POST = handle_request
        do_PATCH = handle_request

    return Handler


class LocalHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        # HTTPServer normally resolves a reverse-DNS hostname here. This app is
        # loopback-only; skipping lookup keeps startup immediate and offline.
        TCPServer.server_bind(self)
        self.server_name = 'localhost'
        self.server_port = self.server_address[1]


def create_server(workshop, port=8000):
    return LocalHTTPServer(('127.0.0.1', port), make_handler(workshop))
