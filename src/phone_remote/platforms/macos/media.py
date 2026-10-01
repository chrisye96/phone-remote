"""macOS：目前只能读音量。系统没有公开的接口读“正在播放”，播放状态和进度保持未知。"""
import time

from ..base import empty_media_state
from .script import osascript


class MediaWatcher:
    def __init__(self):
        self._state = empty_media_state()
        self._read_at = 0.0

    def state(self):
        if time.monotonic() - self._read_at >= 1:
            self._read_at = time.monotonic()
            settings = osascript("get volume settings")  # output volume:50, ..., output muted:false
            fields = dict(part.strip().split(":", 1) for part in settings.split(",") if ":" in part)
            if fields.get("output volume", "").isdigit():
                self._state.update(vol=int(fields["output volume"]),
                                   muted=fields.get("output muted") == "true")
        return self._state

    def seek(self, seconds):
        pass
