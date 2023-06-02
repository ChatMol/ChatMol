import http.server
from http import HTTPStatus
from pymol import cmd
import urllib.parse
import threading
import requests

class PyMOLCommandHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        """Sets headers required for CORS"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-api-key,Content-Type")

    def do_OPTIONS(self):
        """Respond to a OPTIONS request."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/send_message":
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_data = urllib.parse.unquote(post_data.decode())
        
        try:
            cmd.do(post_data)
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Command executed')
        except Exception as e:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def do_GET(self):
        if self.path == "/":
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b'Hello, this is the local Pymol server.')
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

def start_server():
    httpd = http.server.HTTPServer(('localhost', 8101), PyMOLCommandHandler)
    httpd.serve_forever()

def is_http_server_running():
    url = f'http://localhost:8101'
    try:
        response = requests.get(url)
        return True
    except requests.ConnectionError:
        return False

if not is_http_server_running():
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    print("Server started")

