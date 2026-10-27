#!/usr/bin/env python3
"""Local demo server; no third-party Python dependencies. Not a public auth server."""
import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from traceops.agent import run
from traceops.connectors import ConnectorError
from traceops.world import WorldStoreService

ROOT = Path(__file__).resolve().parent


def load_env():
    path = ROOT / '.env.local'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))


def handler_for(store):
    class Handler(BaseHTTPRequestHandler):
        def send(self, code, payload, content_type='application/json'):
            data = json.dumps(payload).encode() if content_type == 'application/json' else payload
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/api/status':
                self.send(200, {'data_mode': os.getenv('TRACEOPS_DATA_MODE', 'sample'),
                                'model_mode': os.getenv('TRACEOPS_MODEL_MODE', 'sample'),
                                'world': store.health(), 'version': '1.0', 'team': 'ALPHA'})
            elif path == '/api/runs':
                self.send(200, store.history())
            elif path.startswith('/api/runs/'):
                parts = path.strip('/').split('/')
                item = store.get(parts[2])
                if not item:
                    self.send(404, {'error': 'Run not found.'})
                elif len(parts) == 4 and parts[3] == 'trace':
                    data = '\n'.join(json.dumps(e) for e in store.events(parts[2])) + '\n'
                    self.send(200, data.encode(), 'application/x-ndjson')
                else:
                    self.send(200, item)
            else:
                name = 'index.html' if path == '/' else path.lstrip('/')
                target = (ROOT / 'web' / name).resolve()
                if target.is_relative_to(ROOT / 'web') and target.is_file():
                    mime = mimetypes.guess_type(target)[0] or 'application/octet-stream'
                    self.send(200, target.read_bytes(), mime)
                else:
                    self.send(404, {'error': 'Not found.'})

        def do_POST(self):
            # Reject cross-origin browser requests; this app is intentionally loopback-only.
            origin = self.headers.get('Origin')
            host = self.headers.get('Host')
            if origin and origin not in ('http://' + host, 'https://' + host):
                self.send(403, {'error': 'Cross-origin requests are not allowed.'})
                return
            if self.path != '/api/investigate':
                self.send(404, {'error': 'Not found.'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 4096:
                    raise ValueError('Request must contain a JSON body under 4 KB.')
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError('Expected a JSON object.')
                self.send(200, run(store, body.get('question')))
            except (ValueError, TypeError, ConnectorError) as exc:
                self.send(400, {'error': str(exc)})
            except Exception:
                self.send(500, {'error': 'Internal investigation failure. Check server console.'})
                import traceback
                traceback.print_exc()
    return Handler


if __name__ == '__main__':
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.getenv('TRACEOPS_PORT', '8765')))
    args = parser.parse_args()
    store = WorldStoreService(ROOT / 'runtime' / 'world.sqlite3')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(store))
    print(f'TraceOps → http://127.0.0.1:{args.port} (data={os.getenv("TRACEOPS_DATA_MODE", "sample")}, model={os.getenv("TRACEOPS_MODEL_MODE", "sample")})', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
