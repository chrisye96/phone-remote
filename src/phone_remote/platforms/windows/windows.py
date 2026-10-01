"""Windows：列出窗口，把指定窗口切到最前。"""
import ctypes
import os

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi
HWND = ctypes.c_void_p
ENUM_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, HWND, ctypes.c_void_p)
KEYUP = 0x0002

for _fn in ("IsWindowVisible", "IsWindow", "IsIconic", "SetForegroundWindow",
            "BringWindowToTop", "GetWindowTextLengthW"):
    getattr(user32, _fn).argtypes = [HWND]
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
