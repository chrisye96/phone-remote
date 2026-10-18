"""The Windows media watcher, fed fake system media sessions (real ones need an app that is playing)."""
import asyncio
import datetime
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from phone_remote.platforms.base import empty_media_state

if sys.platform == "win32":
    from phone_remote.platforms.windows import media

HAS_WINRT = sys.platform == "win32" and media.SessionManager is not None


class FakeSession:
    def __init__(self, title="Video", playing=True, rate=1.0, position=0.0, age=0.0, duration=300.0,
                 app="chrome.exe"):
        self.title, self.calls, self.source_app_user_model_id = title, [], app
        self._info = SimpleNamespace(playback_status=media.Status.PLAYING if playing else media.Status.PAUSED,
                                     playback_rate=rate)
        self._timeline = SimpleNamespace(
            end_time=datetime.timedelta(seconds=duration), position=datetime.timedelta(seconds=position),
            last_updated_time=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=age))

    def get_playback_info(self):
        return self._info

    def get_timeline_properties(self):
        return self._timeline

    async def try_get_media_properties_async(self):
        return SimpleNamespace(title=self.title, artist="", album_title="")

    async def try_toggle_play_pause_async(self):
        self.calls.append("toggle")

    async def try_play_async(self):
        self.calls.append("play")

    async def try_pause_async(self):
        self.calls.append("pause")

    async def try_change_playback_position_async(self, ticks):
        self.calls.append(("seek", ticks / 10_000_000))

    def pause(self):
        self._info.playback_status = media.Status.PAUSED


def read(session, watcher=None, current=None, sessions=None, front=""):
    """What the watcher shows; current is what Windows calls current, sessions all it knows of,
    front the program whose window is in front."""
    manager = SimpleNamespace(get_current_session=lambda: current or session,
                              get_sessions=lambda: sessions or [session])
    state = empty_media_state()
    with mock.patch.object(media, "front_app", lambda: front):
        asyncio.run((watcher or media.MediaWatcher())._read_session(manager, state))
    return state


def press(session, play=None, title=None):
    asyncio.run(media.MediaWatcher()._toggle(session, play, title))
    return session.calls


@unittest.skipUnless(HAS_WINRT, "needs Windows and the winrt library")
class PositionTest(unittest.TestCase):
    def test_position_advances_while_playing(self):
        state = read(FakeSession(position=10, age=5))
        self.assertAlmostEqual(state["pos"], 15, delta=0.3)
        self.assertEqual(state["rate"], 1)

    def test_position_stands_still_while_the_video_is_stuck_loading(self):
        # A browser keeps saying "playing" while it waits for data, and reports a speed of 0
        state = read(FakeSession(rate=0.0, position=18.1, age=20))
        self.assertIs(state["playing"], True)
        self.assertEqual(state["pos"], 18.1)
        self.assertEqual(state["rate"], 0)

    def test_an_app_that_reports_no_speed_plays_at_normal_speed(self):
        self.assertAlmostEqual(read(FakeSession(rate=None, position=10, age=5))["pos"], 15, delta=0.3)

    def test_position_follows_the_playback_speed(self):
        state = read(FakeSession(rate=2.0, position=10, age=5))
        self.assertAlmostEqual(state["pos"], 20, delta=0.6)
        self.assertEqual(state["rate"], 2)

    def test_paused_position_is_what_the_app_reported(self):
        # Browsers report a speed of 0 when paused; the phone must not inherit that for its next play
        state = read(FakeSession(playing=False, rate=0.0, position=42, age=600))
        self.assertEqual((state["playing"], state["pos"], state["rate"]), (False, 42, 1))


@unittest.skipUnless(HAS_WINRT, "needs Windows and the winrt library")
class PressTest(unittest.TestCase):
    def test_a_plain_press_flips_whatever_is_current(self):
        self.assertEqual(press(FakeSession()), ["toggle"])

    def test_the_phone_says_which_way_it_wants_to_go(self):
        self.assertEqual(press(FakeSession(), play=False), ["pause"])
        self.assertEqual(press(FakeSession(playing=False), play=True), ["play"])

    def test_a_press_meant_for_something_else_is_dropped(self):
        # The phone was showing the video in the front tab; since then the browser has moved its
        # one media session to a paused show in a background tab, which must not start playing
        self.assertEqual(press(FakeSession("Paused show", playing=False), play=True, title="Front video"), [])
        self.assertEqual(press(FakeSession("Paused show", playing=False), title="Front video"), [])

    def test_a_press_for_what_the_phone_shows_goes_through(self):
        self.assertEqual(press(FakeSession("Front video"), play=False, title="Front video"), ["pause"])



@unittest.skipUnless(HAS_WINRT, "needs Windows and the winrt library")
class SeveralSessionsTest(unittest.TestCase):
    """Spotify open but idle, a video playing in the browser."""

    def setUp(self):
        self.watcher = media.MediaWatcher()
        self.video = FakeSession("Video", position=600, duration=1800)
        self.song = FakeSession("Song", playing=False, duration=200, app="Spotify.exe")
        self.sessions = [self.song, self.video]

    def show(self, front=""):
        # Windows calls the idle Spotify current, as it often does once nothing plays
        return read(None, self.watcher, current=self.song, sessions=self.sessions, front=front)

    def test_a_paused_video_stays_shown_when_windows_calls_another_app_current(self):
        self.show()
        self.video.pause()
        state = self.show()
        self.assertEqual((state["title"], state["playing"], state["dur"]), ("Video", False, 1800))

    def test_presses_after_the_pause_go_to_the_video(self):
        self.show()
        self.video.pause()
        self.show()
        asyncio.run(self.watcher._toggle(self.watcher._session, True, "Video"))
        asyncio.run(self.watcher._seek(self.watcher._session, 630, "Video"))
        self.assertEqual((self.video.calls, self.song.calls), (["play", ("seek", 630)], []))

    def test_whatever_starts_playing_is_shown(self):
        self.show()
        self.video.pause()
        self.song._info.playback_status = media.Status.PLAYING
        self.assertEqual(self.show()["title"], "Song")

    def test_bringing_a_window_forward_shows_its_paused_media(self):
        # Spotify played and was paused; then its window was minimized and the browser's restored
        self.video.pause()
        self.song._info.playback_status = media.Status.PLAYING
        self.show(front="Spotify")
        self.song.pause()
        self.assertEqual(self.show(front="chrome")["title"], "Video")
        self.assertEqual(self.show(front="Spotify")["title"], "Song")  # and back again

    def test_a_window_left_in_front_does_not_take_over(self):
        # The browser stayed in front while Spotify was played and paused from the phone
        self.show(front="chrome")
        self.video.pause()
        self.song._info.playback_status = media.Status.PLAYING
        self.show(front="chrome")
        self.song.pause()
        self.assertEqual(self.show(front="chrome")["title"], "Song")

    def test_a_seek_meant_for_something_else_is_dropped(self):
        # The phone worked out the position from the song it was showing; the video is current now
        self.show()
        asyncio.run(self.watcher._seek(self.video, 0, "Song"))
        self.assertEqual(self.video.calls, [])


if __name__ == "__main__":
    unittest.main()
