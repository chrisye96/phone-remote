"""Windows：读播放状态、标题、进度和音量，并跳转进度。

播放信息来自系统的“媒体控制”接口，浏览器和大多数播放器都会向它上报。
注意：浏览器上报“播放 / 暂停”可能晚十秒左右，跳转则一秒内就能读到。

需要 winrt 库。没装的话播放状态和进度保持未知，其他功能不受影响。
"""
import asyncio
import datetime
import threading

from ..base import empty_media_state
from . import audio

try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
    )
except ImportError:
    SessionManager = None

POLL_SECONDS = 0.5


class MediaWatcher:
    def __init__(self):
        self._state = empty_media_state()
        self._loop = None
        self._session = None
        self._stopping = False

    def start(self):
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    def stop(self):
        self._stopping = True

    def state(self):
        return self._state

    def seek(self, seconds):
        if self._loop and self._session:
            asyncio.run_coroutine_threadsafe(self._seek(seconds), self._loop)

    async def _seek(self, seconds):
        duration = self._state["dur"]
        if self._session and duration > 0:
            target = max(0, min(duration - 1, seconds))
            try:
                await self._session.try_change_playback_position_async(int(target * 10_000_000))
            except OSError:
                pass

    async def _run(self):
        self._loop = asyncio.get_running_loop()
        audio.init_thread()
        manager = None
        while not self._stopping:
            state = empty_media_state()
            volume = audio.read_volume()
            if volume:
                state["vol"], state["muted"] = volume
            try:
                if manager is None and SessionManager:
                    manager = await SessionManager.request_async()
                if manager:
                    await self._read_session(manager, state)
            except OSError:
                self._session = None
            self._state = state
            await asyncio.sleep(POLL_SECONDS)

    async def _read_session(self, manager, state):
        # 有正在播放的就用它，否则用系统当前的那个
        session = manager.get_current_session()
        for candidate in manager.get_sessions():
            if candidate.get_playback_info().playback_status == Status.PLAYING:
                session = candidate
                break
        self._session = session
        if not session:
            return
        info = session.get_playback_info()
        status = info.playback_status
        state["playing"] = {Status.PLAYING: True, Status.PAUSED: False, Status.STOPPED: False}.get(status)
        try:
            state["title"] = (await session.try_get_media_properties_async()).title or ""
        except OSError:
            pass
        timeline = session.get_timeline_properties()
        duration = timeline.end_time.total_seconds()
        position = timeline.position.total_seconds()
        if duration > 0 and status == Status.PLAYING:
            # 系统只在跳转、暂停时更新进度，播放中的当前位置要自己推算
            elapsed = datetime.datetime.now(datetime.timezone.utc) - timeline.last_updated_time
            position += elapsed.total_seconds() * (info.playback_rate or 1)
        state["pos"] = round(max(0, min(duration, position)), 1)
        state["dur"] = round(duration, 1)
