"""macOS：模拟按键、文字输入和鼠标。需要“辅助功能”权限。"""
import ctypes
import struct
import time

from ...keys import KEYS
from .script import osascript_async

cg = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


_vp = ctypes.c_void_p
cg.CGEventCreateKeyboardEvent.restype = _vp
cg.CGEventCreateKeyboardEvent.argtypes = [_vp, ctypes.c_uint16, ctypes.c_bool]
cg.CGEventSetFlags.argtypes = [_vp, ctypes.c_uint64]
cg.CGEventKeyboardSetUnicodeString.argtypes = [_vp, ctypes.c_ulong, ctypes.POINTER(ctypes.c_uint16)]
cg.CGEventSetIntegerValueField.argtypes = [_vp, ctypes.c_uint32, ctypes.c_int64]
cg.CGEventPost.argtypes = [ctypes.c_uint32, _vp]
cg.CFRelease.argtypes = [_vp]
cg.CGEventCreate.restype = _vp
cg.CGEventCreate.argtypes = [_vp]
cg.CGEventGetLocation.restype = CGPoint
cg.CGEventGetLocation.argtypes = [_vp]
cg.CGEventCreateMouseEvent.restype = _vp
cg.CGEventCreateMouseEvent.argtypes = [_vp, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
cg.CGEventCreateScrollWheelEvent2.restype = _vp
cg.CGEventCreateScrollWheelEvent2.argtypes = [
    _vp, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
cg.AXIsProcessTrusted.restype = ctypes.c_bool

MOD_FLAGS = {"shift": 0x20000, "ctrl": 0x40000, "alt": 0x80000, "win": 0x100000, "mod": 0x100000}
VOLUME_SCRIPTS = {
    "volup": "set volume output volume ((output volume of (get volume settings)) + 6)",
    "voldown": "set volume output volume ((output volume of (get volume settings)) - 6)",
    "mute": "set volume output muted (not (output muted of (get volume settings)))",
}


def has_permission():
    return cg.AXIsProcessTrusted()


def _post(event):
    cg.CGEventPost(0, event)
    cg.CFRelease(event)


def press(mods, name):
    if name in VOLUME_SCRIPTS:
        osascript_async(VOLUME_SCRIPTS[name])
        return
    if name == "media":
        name = "space"
    flags = 0
    for m in mods:
        flags |= MOD_FLAGS[m]
    for down in (True, False):
        event = cg.CGEventCreateKeyboardEvent(None, KEYS[name][1], down)
        if flags:
            cg.CGEventSetFlags(event, flags)
        _post(event)


def type_text(text):
    data = text.encode("utf-16-le")
    units = struct.unpack("<%dH" % (len(data) // 2), data)
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
