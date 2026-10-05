"""HTTP 服务器：给手机提供页面文件，接收并校验手机发来的指令。"""
import hmac
import ipaddress
import json
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .actions import FeatureDisabled
from .pairing import pair_page

WEB_DIR = Path(__file__).parent / "web"
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}
LOCAL_ADDRESSES = ("127.0.0.1", "::1")
MAX_BODY = 65536     # bytes; room for the longest text the phone may send, in any script
AUTH_WINDOW = 60     # seconds a signed command stays valid
MAX_FAILURES = 10    # wrong signatures from one address before it is locked out
LOCKOUT = 300        # seconds the lockout lasts, counted from the first failure


def sign(token, sent, body):
    return hmac.new(token.encode(), sent.encode() + b"\n" + body, "sha256").hexdigest()


class Guard:
    """Refuses replayed or stale commands, and addresses that keep sending wrong signatures."""

    def __init__(self):
        self.lock = threading.Lock()
        self.seen = {}      # signature -> time it can be forgotten
        self.failures = {}  # address -> (count, time of the first failure); only LAN addresses, so it stays small
        self.pruned = 0

    def fresh(self, sent, signature):
        now = time.time()
        try:
            age = abs(int(sent) / 1000 - now)
        except ValueError:
            return False
        with self.lock:
            if now - self.pruned > AUTH_WINDOW:
                self.seen = {s: t for s, t in self.seen.items() if t > now}
                self.pruned = now
            if age > AUTH_WINDOW or signature in self.seen:
                return False
            self.seen[signature] = now + 2 * AUTH_WINDOW  # outlives the window in which it would be accepted
            return True

    def failed(self, address):
        now = time.time()
        with self.lock:
            count, since = self.failures.get(address, (0, now))
            if now - since > LOCKOUT:
                count, since = 0, now
            self.failures[address] = (count + 1, since)

    def blocked(self, address):
        with self.lock:
            count, since = self.failures.get(address, (0, 0))
        return count >= MAX_FAILURES and time.time() - since < LOCKOUT


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def reply(self, status, body=b"", content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.allow_lan_origin()
        self.end_headers()
        self.wfile.write(body)

    def allow_lan_origin(self):
        # A remote page served by another paired computer may send commands here. Only pages that
        # themselves come from a private address are let in, so a website on the internet cannot
        # even try; the signature still guards /api either way.
        origin = self.headers.get("Origin", "")
        try:
            private = ipaddress.ip_address(urlsplit(origin).hostname or "").is_private
        except ValueError:
            private = False
        if private:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        # The browser asks before a page from another origin may send X-Auth
        self.send_response(204)
        self.allow_lan_origin()
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Auth")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/pair":
            if self.client_address[0] not in LOCAL_ADDRESSES:
                return self.reply(404)
            page = pair_page(self.server.phone_url(), self.server.tray_mode, not self.server.has_permission())
            return self.reply(200, page.encode("utf-8"), STATIC_TYPES[".html"])
        self.reply_static("index.html" if path == "/" else path.lstrip("/"))

    def reply_static(self, relative):
        # 只允许 web 目录里、已知类型的文件
        target = (WEB_DIR / relative).resolve()
        content_type = STATIC_TYPES.get(target.suffix)
        if content_type is None or WEB_DIR.resolve() not in target.parents or not target.is_file():
            return self.reply(404)
        self.reply(200, target.read_bytes(), content_type)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if 0 < length < MAX_BODY:
            body = self.rfile.read(length)
        else:
            body = b""
            self.close_connection = True  # 没读的内容不能留在连接里
        if self.path != "/api":
            return self.reply(404)
        if not body and length:
            return self.reply(400)  # too large to read, so there is nothing to check a signature against
        guard, address = self.server.guard, self.client_address[0]
        if guard.blocked(address):
            return self.reply(429)
        # X-Auth is "<milliseconds>.<signature>". The token itself never travels, so someone
        # listening on the network cannot learn it.
        sent, _, signature = self.headers.get("X-Auth", "").partition(".")
        if not hmac.compare_digest(signature.encode(), sign(self.server.token, sent, body).encode()):
            guard.failed(address)
            return self.reply(403)
        if not guard.fresh(sent, signature):
            # Signed correctly but too old, or already used. Tell the phone our clock so it can retry.
            return self.reply(401, json.dumps({"now": int(time.time() * 1000)}).encode(), "application/json")
        try:
            result = self.server.dispatcher.handle(json.loads(body))
        except FeatureDisabled:
            return self.reply(423)
        except (ValueError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
            return self.reply(400)
        if result is None:
            return self.reply(204)
        self.reply(200, json.dumps(result).encode("utf-8"), "application/json")


class Server(ThreadingHTTPServer):
    # 默认会允许重复占用端口，在 Windows 上这意味着能同时启动两个，手机会随机连到其中一个
    allow_reuse_address = False


def make_server(port, token, dispatcher, phone_url=lambda: ""):
    """phone_url is called whenever the QR page is shown, so it can follow a changed address or token."""
    server = Server(("0.0.0.0", port), Handler)
    server.token = token
    server.guard = Guard()
    server.dispatcher = dispatcher
    server.phone_url = phone_url
    server.tray_mode = False  # 决定二维码页面上提示“托盘”还是“命令行窗口”
    server.has_permission = lambda: True  # asked each time the QR page is shown; the page explains when it says no
    return server
