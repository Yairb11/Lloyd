from pathlib import Path
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PyQt6.QtCore import QObject, pyqtSignal

from app.config import PHONE_SCAN_UPLOAD_DIR
from app.network.html import SCAN_PHONE

UPLOAD_DIR = Path(PHONE_SCAN_UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        local_ip = sock.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        sock.close()
    return local_ip


class ServerBridge(QObject):
    image_received = pyqtSignal(str)


class PhoneUploadServer(ThreadingHTTPServer):
    def __init__(self, server_address, request_handler_class, bridge: ServerBridge):
        super().__init__(server_address, request_handler_class)
        self.bridge = bridge


class PhoneUploadHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        encoded_html = SCAN_PHONE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_html)))
        self.end_headers()
        self.wfile.write(encoded_html)

    def do_POST(self):
        if self.path == "/upload":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                return

            file_bytes = self.rfile.read(content_length)

            timestamp = int(time.time() * 1000)
            saved_path = UPLOAD_DIR / f"scan_{timestamp}.jpg"
            with open(saved_path, "wb") as f:
                f.write(file_bytes)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"received"}')


            if hasattr(self.server, "bridge") and self.server.bridge:
                self.server.bridge.image_received.emit(str(saved_path.resolve()))
        else:
            self.send_response(404)
            self.end_headers()
