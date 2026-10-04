"""Windows 实现。"""
from ..base import Platform
from . import input as _input
from . import windows as _windows
from .media import MediaWatcher


class WindowsPlatform(Platform):
    name = "win"

    def __init__(self):
        self._media = MediaWatcher()

    def start(self):
        self._media.start()

    def stop(self):
        self._media.stop()

    press = staticmethod(_input.press)
    type_text = staticmethod(_input.type_text)
    mouse_move = staticmethod(_input.mouse_move)
    mouse_click = staticmethod(_input.mouse_click)
    mouse_button = staticmethod(_input.mouse_button)
    mouse_scroll = staticmethod(_input.mouse_scroll)
    list_windows = staticmethod(_windows.list_windows)
    focus_window = staticmethod(_windows.focus_window)

    def media_state(self):
        return self._media.state()

    def media_toggle(self, play=None, title=None):
        return self._media.toggle(play, title)

    def media_seek(self, seconds):
        self._media.seek(seconds)
