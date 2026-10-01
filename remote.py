"""手机遥控器：在电脑上运行，手机浏览器打开网页来控制视频播放。

只用 Python 标准库，Windows 和 macOS 通用。
用法：python remote.py
"""
import base64
import ctypes
import json
import os
import secrets
import socket
import struct
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("REMOTE_PORT", 8765))
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, "token.txt")
SYSTEM_KEYS = ("volup", "voldown", "mute", "media")
MODIFIERS = ("ctrl", "shift", "alt", "win", "mod")  # mod = Windows 的 Ctrl / Mac 的 Command

# 按键名: (Windows 虚拟键码, macOS 键码)
KEYS = {
    "space": (0x20, 49), "enter": (0x0D, 36), "esc": (0x1B, 53), "tab": (0x09, 48),
    "backspace": (0x08, 51), "delete": (0x2E, 117),
    "left": (0x25, 123), "right": (0x27, 124), "up": (0x26, 126), "down": (0x28, 125),
    "pageup": (0x21, 116), "pagedown": (0x22, 121), "home": (0x24, 115), "end": (0x23, 119),
    "[": (0xDB, 33), "]": (0xDD, 30), ",": (0xBC, 43), ".": (0xBE, 47), "/": (0xBF, 44),
    ";": (0xBA, 41), "'": (0xDE, 39), "-": (0xBD, 27), "=": (0xBB, 24), "`": (0xC0, 50),
}
MAC_LETTERS = dict(a=0, s=1, d=2, f=3, h=4, g=5, z=6, x=7, c=8, v=9, b=11, q=12, w=13,
                   e=14, r=15, y=16, t=17, o=31, u=32, i=34, p=35, l=37, j=38, k=40, n=45, m=46)
MAC_DIGITS = [29, 18, 19, 20, 21, 23, 22, 26, 28, 25]
# F13 以后键盘上没有，留给浏览器助手扩展当指令用；Mac 只到 F20（-1 表示没有）
MAC_FKEYS = [122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111,
             105, 107, 113, 106, 64, 79, 80, 90, -1, -1, -1, -1]
for letter, code in MAC_LETTERS.items():
    KEYS[letter] = (ord(letter.upper()), code)
for digit, code in enumerate(MAC_DIGITS):
    KEYS[str(digit)] = (0x30 + digit, code)
for n, code in enumerate(MAC_FKEYS):
    KEYS["f%d" % (n + 1)] = (0x70 + n, code)


# 电脑上的播放状态：playing 为 True / False，读不到时为 None
MEDIA = {"playing": None, "title": ""}


def parse_combo(combo):
    """'ctrl+shift+n' -> (['ctrl', 'shift'], 'n')"""
    *mods, name = str(combo).lower().split("+")
    if any(m not in MODIFIERS for m in mods):
        raise ValueError("unknown modifier")
    if name not in KEYS and not (name in SYSTEM_KEYS and not mods):
        raise ValueError("unknown key")
    return mods, name


def utf16_units(text):
    data = text.encode("utf-16-le")
    return struct.unpack("<%dH" % (len(data) // 2), data)


if sys.platform == "win32":
    PLATFORM = "win"
    user32 = ctypes.windll.user32
    KEYUP = 0x0002
    EXTENDED = 0x0001
    UNICODE = 0x0004
    EXTENDED_KEYS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2E, 0x5B}
    WIN_SYSTEM = {"volup": 0xAF, "voldown": 0xAE, "mute": 0xAD, "media": 0xB3}
    WIN_MODS = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B, "mod": 0x11}

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.c_void_p)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_void_p)]

    class INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]
        _anonymous_ = ("u",)
        _fields_ = [("type", ctypes.c_ulong), ("u", _U)]

    def _key(vk, down):
        flags = EXTENDED if vk in EXTENDED_KEYS else 0
        user32.keybd_event(vk, 0, flags if down else flags | KEYUP, 0)

    def press(combo):
        mods, name = parse_combo(combo)
        vk = WIN_SYSTEM[name] if name in WIN_SYSTEM else KEYS[name][0]
        held = [WIN_MODS[m] for m in mods]
        for m in held:
            _key(m, True)
        _key(vk, True)
        _key(vk, False)
        for m in reversed(held):
            _key(m, False)

    def type_text(text):
        units = utf16_units(text)
        inputs = (INPUT * (2 * len(units)))()
        for i, unit in enumerate(units):
            for j, flags in enumerate((UNICODE, UNICODE | KEYUP)):
                item = inputs[2 * i + j]
                item.type = 1
                item.ki.wScan = unit
                item.ki.dwFlags = flags
        user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))

    def mouse_move(dx, dy):
        user32.mouse_event(0x0001, dx, dy, 0, 0)

    def mouse_click(right=False):
        down, up = (0x0008, 0x0010) if right else (0x0002, 0x0004)
        user32.mouse_event(down, 0, 0, 0, 0)
        user32.mouse_event(up, 0, 0, 0, 0)

    def mouse_scroll(dy):
        # 滚轮一格是 120，大约对应 100 像素
        user32.mouse_event(0x0800, 0, 0, int(dy * 1.2), 0)

    kernel32 = ctypes.windll.kernel32
    dwmapi = ctypes.windll.dwmapi
    HWND = ctypes.c_void_p
    ENUM_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, HWND, ctypes.c_void_p)
    for fn in ("IsWindowVisible", "IsWindow", "IsIconic", "SetForegroundWindow",
               "BringWindowToTop", "GetWindowTextLengthW"):
        getattr(user32, fn).argtypes = [HWND]
    user32.GetForegroundWindow.restype = HWND
    user32.GetWindow.restype = HWND
    user32.GetWindow.argtypes = [HWND, ctypes.c_uint]
    user32.GetWindowLongW.argtypes = [HWND, ctypes.c_int]
    user32.GetWindowTextW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetClassNameW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
    user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(ctypes.c_ulong)]
    user32.EnumWindows.argtypes = [ENUM_PROC, ctypes.c_void_p]
    user32.AttachThreadInput.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_bool]
    dwmapi.DwmGetWindowAttribute.argtypes = [HWND, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_ulong]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.QueryFullProcessImageNameW.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]

    def _app_name(hwnd):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return ""
        buf = ctypes.create_unicode_buffer(520)
        size = ctypes.c_ulong(520)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
        kernel32.CloseHandle(handle)
        return os.path.splitext(os.path.basename(buf.value))[0] if ok else ""

    def list_windows():
        """任务栏上能看到的窗口，按从前到后的顺序。"""
        found = []
        front = user32.GetForegroundWindow()

        def visit(hwnd, _):
            if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, 4):
                return True
            if user32.GetWindowLongW(hwnd, -20) & 0x80:  # 工具窗口
                return True
            cloaked = ctypes.c_int(0)
            dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), 4)
            length = user32.GetWindowTextLengthW(hwnd)
            if cloaked.value or not length:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value != "Progman":
                found.append({"id": hwnd, "title": title.value, "app": _app_name(hwnd),
                              "active": hwnd == front})
            return True

        user32.EnumWindows(ENUM_PROC(visit), None)
        return found

    def focus_window(hwnd):
        hwnd = int(hwnd)
        if not user32.IsWindow(hwnd):
            raise ValueError("no such window")
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        # Windows 只让“刚收到过输入”的进程抢前台，先发一个没有任何作用的按键
        user32.keybd_event(0xE8, 0, 0, 0)
        user32.keybd_event(0xE8, 0, KEYUP, 0)
        user32.SetForegroundWindow(hwnd)
        if user32.GetForegroundWindow() != hwnd:
            ours = kernel32.GetCurrentThreadId()
            theirs = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
            user32.AttachThreadInput(ours, theirs, True)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(ours, theirs, False)

    # 用系统的“媒体控制”接口读播放状态（浏览器和大多数播放器都会上报）。
    # 这个接口只能从 PowerShell 里方便地调用，所以常驻一个子进程，状态变了就输出一行。
    MEDIA_SCRIPT = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
$mgrType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]
$propsType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType=WindowsRuntime]
$mgr = Await ($mgrType::RequestAsync()) $mgrType
$last = ''
while (Get-Process -Id PARENT_PID -ErrorAction SilentlyContinue) {
  $line = 'None'
  try {
    $pick = $mgr.GetCurrentSession()
    foreach ($s in $mgr.GetSessions()) { if ("$($s.GetPlaybackInfo().PlaybackStatus)" -eq 'Playing') { $pick = $s; break } }
    if ($pick) {
      $title = ''
      try { $title = (Await ($pick.TryGetMediaPropertiesAsync()) $propsType).Title } catch {}
      $line = "$($pick.GetPlaybackInfo().PlaybackStatus)`t$title"
    }
  } catch {}
  if ($line -ne $last) { [Console]::Out.WriteLine($line); $last = $line }
  Start-Sleep -Milliseconds 600
}
"""

    def start_media_watch():
        script = MEDIA_SCRIPT.replace("PARENT_PID", str(os.getpid()))
        exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                           "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        try:
            proc = subprocess.Popen(
                [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                encoding="utf-8", errors="replace", creationflags=0x08000000)
        except OSError:
            return

        def read():
            for line in proc.stdout:
                status, _, title = line.rstrip("\r\n").partition("\t")
                MEDIA["playing"] = {"Playing": True, "Paused": False, "Stopped": False}.get(status)
                MEDIA["title"] = title

        threading.Thread(target=read, daemon=True).start()

    def check_permission():
        return True

elif sys.platform == "darwin":
    PLATFORM = "mac"
    cg = ctypes.CDLL(
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
    )

    class CGPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    vp = ctypes.c_void_p
    cg.CGEventCreateKeyboardEvent.restype = vp
    cg.CGEventCreateKeyboardEvent.argtypes = [vp, ctypes.c_uint16, ctypes.c_bool]
    cg.CGEventSetFlags.argtypes = [vp, ctypes.c_uint64]
    cg.CGEventKeyboardSetUnicodeString.argtypes = [
        vp, ctypes.c_ulong, ctypes.POINTER(ctypes.c_uint16)]
    cg.CGEventSetIntegerValueField.argtypes = [vp, ctypes.c_uint32, ctypes.c_int64]
    cg.CGEventPost.argtypes = [ctypes.c_uint32, vp]
    cg.CFRelease.argtypes = [vp]
    cg.CGEventCreate.restype = vp
    cg.CGEventCreate.argtypes = [vp]
    cg.CGEventGetLocation.restype = CGPoint
    cg.CGEventGetLocation.argtypes = [vp]
    cg.CGEventCreateMouseEvent.restype = vp
    cg.CGEventCreateMouseEvent.argtypes = [vp, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
    cg.CGEventCreateScrollWheelEvent2.restype = vp
    cg.CGEventCreateScrollWheelEvent2.argtypes = [
        vp, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
    ]
    cg.AXIsProcessTrusted.restype = ctypes.c_bool
    MAC_MODS = {"shift": 0x20000, "ctrl": 0x40000, "alt": 0x80000,
                "win": 0x100000, "mod": 0x100000}
    VOLUME_SCRIPTS = {
        "volup": "set volume output volume ((output volume of (get volume settings)) + 6)",
        "voldown": "set volume output volume ((output volume of (get volume settings)) - 6)",
        "mute": "set volume output muted (not (output muted of (get volume settings)))",
    }

    def _post(event):
        cg.CGEventPost(0, event)
        cg.CFRelease(event)

    def press(combo):
        mods, name = parse_combo(combo)
        if name in VOLUME_SCRIPTS:
            subprocess.Popen(["osascript", "-e", VOLUME_SCRIPTS[name]])
            return
        if name == "media":
            name = "space"
        if KEYS[name][1] < 0:
            raise ValueError("key not available on macOS")
        flags = 0
        for m in mods:
            flags |= MAC_MODS[m]
        for down in (True, False):
            event = cg.CGEventCreateKeyboardEvent(None, KEYS[name][1], down)
            if flags:
                cg.CGEventSetFlags(event, flags)
            _post(event)

    def type_text(text):
        units = utf16_units(text)
        for start in range(0, len(units), 20):
            chunk = units[start:start + 20]
            buf = (ctypes.c_uint16 * len(chunk))(*chunk)
            for down in (True, False):
                event = cg.CGEventCreateKeyboardEvent(None, 0, down)
                cg.CGEventKeyboardSetUnicodeString(event, len(chunk), buf)
                _post(event)

    def _cursor():
        event = cg.CGEventCreate(None)
        point = cg.CGEventGetLocation(event)
        cg.CFRelease(event)
        return point

    def mouse_move(dx, dy):
        point = _cursor()
        point.x += dx
        point.y += dy
        _post(cg.CGEventCreateMouseEvent(None, 5, point, 0))

    _last_click = [0.0]

    def mouse_click(right=False):
        point = _cursor()
        down, up, button = (3, 4, 1) if right else (1, 2, 0)
        # macOS 靠事件里的点击计数识别双击，两次单击不会自动算双击
        now = time.monotonic()
        count = 2 if not right and now - _last_click[0] < 0.4 else 1
        _last_click[0] = 0.0 if count == 2 else now
        for kind in (down, up):
            event = cg.CGEventCreateMouseEvent(None, kind, point, button)
            cg.CGEventSetIntegerValueField(event, 1, count)
            _post(event)

    def mouse_scroll(dy):
        _post(cg.CGEventCreateScrollWheelEvent2(None, 0, 1, dy, 0, 0))

    def _osascript(*lines, args=()):
        cmd = ["osascript"]
        for line in lines:
            cmd += ["-e", line]
        result = subprocess.run(cmd + list(args), capture_output=True, text=True, timeout=5)
        return result.stdout.strip()

    def list_windows():
        """Mac 上按应用切换：列出有界面的应用。"""
        names = _osascript('tell application "System Events" to get name of every process '
                           'whose background only is false')
        front = _osascript('tell application "System Events" to get name of first process '
                           'whose frontmost is true')
        return [{"id": name, "title": name, "app": "", "active": name == front}
                for name in (n.strip() for n in names.split(",")) if name]

    def focus_window(name):
        if name not in [w["id"] for w in list_windows()]:
            raise ValueError("no such app")
        _osascript("on run argv",
                   'tell application "System Events" to set frontmost of process (item 1 of argv) to true',
                   "end run", args=[name])

    def start_media_watch():
        pass  # macOS 没有公开的接口读“正在播放”，状态保持未知

    def check_permission():
        return cg.AXIsProcessTrusted()

else:
    sys.exit("只支持 Windows 和 macOS。")


# 定时暂停：到点后如果还在播放，就按一下系统播放键
TIMER = {"until": 0.0, "handle": None}


def timer_fired():
    TIMER.update(until=0.0, handle=None)
    if MEDIA["playing"] is not False:
        press("media")


def set_timer(minutes):
    if not 0 <= minutes <= 600:
        raise ValueError("bad timer")
    if TIMER["handle"]:
        TIMER["handle"].cancel()
    TIMER.update(until=0.0, handle=None)
    if minutes:
        handle = threading.Timer(minutes * 60, timer_fired)
        handle.daemon = True
        handle.start()
        TIMER.update(until=time.time() + minutes * 60, handle=handle)


def clamp(value, limit):
    return max(-limit, min(limit, int(value)))


def handle_action(msg):
    action = msg.get("a")
    if action == "ping":
        pass
    elif action == "state":
        return dict(MEDIA, timer=max(0, int(TIMER["until"] - time.time())))
    elif action == "timer":
        set_timer(float(msg.get("min", 0)))
    elif action == "open":
        url = str(msg.get("url", ""))
        if not url.startswith(("https://", "http://")):
            raise ValueError("bad url")
        webbrowser.open(url)
    elif action == "windows":
        return list_windows()
    elif action == "focus":
        focus_window(msg.get("id"))
    elif action == "key":
        press(msg.get("k"))
    elif action == "text":
        text = " ".join(str(msg.get("t", "")).split())[:2000]
        if text:
            type_text(text)
        if msg.get("enter"):
            press("enter")
    elif action == "move":
        mouse_move(clamp(msg.get("dx", 0), 2000), clamp(msg.get("dy", 0), 2000))
    elif action == "click":
        mouse_click(right=bool(msg.get("right")))
    elif action == "scroll":
        mouse_scroll(clamp(msg.get("dy", 0), 1500))
    else:
        raise ValueError("unknown action")


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            return token
    token = secrets.token_hex(8)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token)
    return token


def lan_ip():
    # 不会真的发送数据，只是让系统选出通往局域网的网卡地址
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


PAIR_PAGE = """<!doctype html><html lang="zh"><meta charset="utf-8"><title>手机遥控器</title>
<style>body{font-family:system-ui,sans-serif;background:#14161a;color:#eee;text-align:center;padding:48px}
#qr{display:inline-block;background:#fff;padding:16px;border-radius:12px;margin:24px}
code{font-size:20px;background:#262a31;padding:8px 14px;border-radius:8px}p{color:#aab}</style>
<h1>用 iPhone 相机扫码</h1><div id="qr"></div>
<p>手机和这台电脑要连同一个 Wi-Fi。扫不了就在手机浏览器里输入：</p><code>__URL__</code>
<p>打开后可以在 Safari 里“添加到主屏幕”，下次直接点图标。<br>这个页面可以关掉，但不要关闭遥控器的黑色窗口。</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>new QRCode(document.getElementById("qr"),{text:"__URL__",width:260,height:260})</script></html>"""


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
        if path == "/":
            with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
                page = f.read().replace("__PLATFORM__", PLATFORM)
            page = page.replace("__HOST__", json.dumps(socket.gethostname()))
            self.reply(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/pair" and self.client_address[0] == "127.0.0.1":
            page = PAIR_PAGE.replace("__URL__", self.server.phone_url)
            self.reply(200, page.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self.reply(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if 0 < length < 16384 else b""
        if self.path != "/api":
            return self.reply(404)
        if not secrets.compare_digest(self.headers.get("X-Token", ""), self.server.token):
            return self.reply(403)
        try:
            result = handle_action(json.loads(body))
        except (ValueError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
            return self.reply(400)
        if result is None:
            return self.reply(204)
        self.reply(200, json.dumps(result).encode("utf-8"), "application/json")


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.token = load_token()
    server.phone_url = "http://%s:%d/#%s" % (lan_ip(), PORT, server.token)
    print("手机遥控器已启动。手机打开这个网址（或扫电脑上弹出的二维码）：")
    print("  " + server.phone_url)
    if not check_permission():
        print("\n还没有控制权限：打开 系统设置 > 隐私与安全性 > 辅助功能，")
        print("把运行本程序的“终端”打开，然后重新启动本程序。")
    print("\n用的时候保持这个窗口开着，关掉窗口就是退出。")
    start_media_watch()
    if "--no-browser" not in sys.argv:
        webbrowser.open("http://127.0.0.1:%d/pair" % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
