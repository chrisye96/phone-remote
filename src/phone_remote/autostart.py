"""开机自动启动的开关。默认关，由托盘菜单打开。

Windows 写注册表里当前用户的“启动”项；macOS 写一个 LaunchAgent。
"""
import plistlib
import sys
from pathlib import Path

ENTRY_NAME = "PhoneRemote"
MAC_LABEL = "local.phone-remote"


def launch_command():
    """开机时要运行的命令。--background 表示不弹二维码页面。"""
    if getattr(sys, "frozen", False):  # 打包后的程序
        return [sys.executable, "--background"]
    executable = Path(sys.executable)
    windowless = executable.with_name("pythonw.exe")  # 不带黑窗口的 Python
    if windowless.exists():
        executable = windowless
    return [str(executable), "-m", "phone_remote", "--background"]


if sys.platform == "win32":
    import subprocess
    import winreg

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_enabled(name=ENTRY_NAME):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, name)
            return True
        except OSError:
            return False

    def set_enabled(enabled, name=ENTRY_NAME):
        # CreateKeyEx opens the key, and makes it first on a fresh account that has no Run key yet
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, subprocess.list2cmdline(launch_command()))
            elif is_enabled(name):
                winreg.DeleteValue(key, name)

else:
    def _plist_path():
        return Path.home() / "Library" / "LaunchAgents" / (MAC_LABEL + ".plist")

    def is_enabled(name=ENTRY_NAME):
        return _plist_path().exists()

    def set_enabled(enabled, name=ENTRY_NAME):
        path = _plist_path()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                plistlib.dump({"Label": MAC_LABEL, "ProgramArguments": launch_command(),
                               "RunAtLoad": True}, f)
        elif path.exists():
            path.unlink()
