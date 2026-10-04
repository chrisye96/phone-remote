"""Windows：模拟按键、文字输入和鼠标。"""
import ctypes
import struct

from ...keys import KEYS

user32 = ctypes.windll.user32
KEYUP = 0x0002
EXTENDED = 0x0001
UNICODE = 0x0004
EXTENDED_KEYS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2E, 0x5B}
SYSTEM_VK = {"volup": 0xAF, "voldown": 0xAE, "mute": 0xAD, "media": 0xB3, "next": 0xB0, "prev": 0xB1}
MOD_VK = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B, "mod": 0x11}


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


def press(mods, name):
    vk = SYSTEM_VK[name] if name in SYSTEM_VK else KEYS[name][0]
    held = [MOD_VK[m] for m in mods]
    for m in held:
        _key(m, True)
    _key(vk, True)
    _key(vk, False)
    for m in reversed(held):
        _key(m, False)


def type_text(text):
    data = text.encode("utf-16-le")
    units = struct.unpack("<%dH" % (len(data) // 2), data)
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


def mouse_button(down):
    user32.mouse_event(0x0002 if down else 0x0004, 0, 0, 0, 0)


def mouse_scroll(dy):
    # 滚轮一格是 120，大约对应 100 像素
    user32.mouse_event(0x0800, 0, 0, int(dy * 1.2), 0)
