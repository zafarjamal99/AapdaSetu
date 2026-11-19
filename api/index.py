"""
==========================================================================
VERCEL SERVERLESS FUNCTION HANDLER FOR AEGIS-MESH BACKEND
Compatible with Vercel Python runtime (BaseHTTPRequestHandler pattern).

Fixes applied:
  - do_OPTIONS: Handles CORS preflight requests (required for POST from browser).
  - HTTP status codes: Returns correct status (200/404/405) rather than always 200.
  - CORS headers: Sent on every response, including OPTIONS.
==========================================================================
"""

import sys
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Include backend in sys.path so app.* imports resolve correctly in Vercel serverless
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.api.endpoints import handle_api_request

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
}


class handler(BaseHTTPRequestHandler):

    def _send_cors_headers(self):
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        """Handle CORS preflight requests from the browser."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)
        params = {k: v[0] for k, v in query_params.items()}

        response_data = handle_api_request(path, method='GET', payload=params)

        # Determine HTTP status from response
        status_code = 200
        if 'error' in response_data and response_data.get('status') == 404:
            status_code = 404

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'

        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            payload = {}

        response_data = handle_api_request(path, method='POST', payload=payload)

        # Determine HTTP status from response
        status_code = 200
        if 'error' in response_data and response_data.get('status') == 404:
            status_code = 404

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress default HTTP server log noise in Vercel logs."""
        pass
