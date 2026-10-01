"""按当前操作系统选择实现。其他代码只通过 base.Platform 的接口调用。"""
import sys

from .base import Platform


def get_platform() -> Platform:
    if sys.platform == "win32":
        from .windows import WindowsPlatform
        return WindowsPlatform()
    if sys.platform == "darwin":
        from .macos import MacPlatform
        return MacPlatform()
    raise SystemExit("只支持 Windows 和 macOS。")
