"""The Windows media watcher, fed fake system media sessions (real ones need an app that is playing)."""
import asyncio
import datetime
import sys
import unittest
from types import SimpleNamespace

from phone_remote.platforms.base import empty_media_state

if sys.platform == "win32":
    from phone_remote.platforms.windows import media

HAS_WINRT = sys.platform == "win32" and media.SessionManager is not None


class FakeSession:
    source_app_user_model_id = "chrome.exe"

    def __init__(self, title="Video", playing=True, rate=1.0, position=0.0, age=0.0, duration=300.0):
        self.title, self.calls = title, []
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


def read(session):
    manager = SimpleNamespace(get_current_session=lambda: session, get_sessions=lambda: [session])
    state = empty_media_state()
    asyncio.run(media.MediaWatcher()._read_session(manager, state))
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


if __name__ == "__main__":
    unittest.main()
