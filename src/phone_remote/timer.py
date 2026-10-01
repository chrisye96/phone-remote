"""定时暂停：到点后如果还在播放，就按一下系统播放键。"""
import threading
import time


class SleepTimer:
    def __init__(self, platform):
        self._platform = platform
        self._until = 0.0
        self._handle = None

    def remaining(self):
        return max(0, int(self._until - time.time()))

    def set(self, minutes):
        if not 0 <= minutes <= 600:
            raise ValueError("bad timer")
        if self._handle:
            self._handle.cancel()
        self._until, self._handle = 0.0, None
        if minutes:
            self._handle = threading.Timer(minutes * 60, self._fired)
            self._handle.daemon = True
            self._handle.start()
            self._until = time.time() + minutes * 60

    def _fired(self):
        self._until, self._handle = 0.0, None
        if self._platform.media_state()["playing"] is not False:
            self._platform.press([], "media")
