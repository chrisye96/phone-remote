"""HTTP 服务器：给手机提供页面文件，接收并校验手机发来的指令。"""
import json
import secrets
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

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


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def reply(self, status, body=b"", content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/pair":
            if self.client_address[0] not in LOCAL_ADDRESSES:
                return self.reply(404)
            page = pair_page(self.server.phone_url, self.server.tray_mode)
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
        if 0 < length < 16384:
            body = self.rfile.read(length)
        else:
            body = b""
            self.close_connection = True  # 没读的内容不能留在连接里
        if self.path != "/api":
            return self.reply(404)
        if not secrets.compare_digest(self.headers.get("X-Token", ""), self.server.token):
            return self.reply(403)
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


def make_server(port, token, dispatcher, phone_url=""):
    server = Server(("0.0.0.0", port), Handler)
    server.token = token
    server.dispatcher = dispatcher
    server.phone_url = phone_url
    server.tray_mode = False  # 决定二维码页面上提示“托盘”还是“命令行窗口”
    return server
