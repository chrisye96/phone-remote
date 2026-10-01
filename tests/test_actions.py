import unittest

from fakes import FakePlatform
from phone_remote.actions import Dispatcher, FeatureDisabled
from phone_remote.config import FEATURES


def make(**overrides):
    platform = FakePlatform()
    opened = []
    features = dict.fromkeys(FEATURES, True)
    features.update(overrides)
    return Dispatcher(platform, features, opener=opened.append), platform, opened


class DispatcherTest(unittest.TestCase):
    def test_key_is_parsed_and_pressed(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "key", "k": "ctrl+shift+tab"})
        self.assertEqual(platform.calls, [("press", ["ctrl", "shift"], "tab")])

    def test_unknown_key_and_action_are_rejected(self):
        dispatcher, platform, _ = make()
        for msg in ({"a": "key", "k": "zzz"}, {"a": "nope"}, {}, {"a": "_do_key"}):
            with self.subTest(msg=msg), self.assertRaises(ValueError):
                dispatcher.handle(msg)
        self.assertEqual(platform.calls, [])

    def test_mouse_values_are_clamped(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "move", "dx": 99999, "dy": -99999})
        dispatcher.handle({"a": "scroll", "dy": 99999})
        dispatcher.handle({"a": "click", "right": True})
        self.assertEqual(platform.calls, [("mouse_move", 2000, -2000), ("mouse_scroll", 1500),
                                          ("mouse_click", True)])

    def test_text_is_collapsed_and_enter_is_optional(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "text", "t": "  hello \n  world  ", "enter": True})
        dispatcher.handle({"a": "text", "t": "   "})
        self.assertEqual(platform.calls, [("type_text", "hello world"), ("press", [], "enter")])

    def test_text_is_capped(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "text", "t": "x" * 5000})
        self.assertEqual(len(platform.calls[0][1]), 2000)

    def test_open_only_accepts_web_urls(self):
        dispatcher, _, opened = make()
        dispatcher.handle({"a": "open", "url": "https://www.bilibili.com"})
        for bad in ("file:///c:/x", "javascript:alert(1)", ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dispatcher.handle({"a": "open", "url": bad})
        self.assertEqual(opened, ["https://www.bilibili.com"])

    def test_timer_range(self):
        dispatcher, _, _ = make()
        dispatcher.handle({"a": "timer", "min": 30})
        self.assertGreater(dispatcher.handle({"a": "state"})["timer"], 1700)
        dispatcher.handle({"a": "timer", "min": 0})
        self.assertEqual(dispatcher.handle({"a": "state"})["timer"], 0)
        with self.assertRaises(ValueError):
            dispatcher.handle({"a": "timer", "min": -5})

    def test_timer_pauses_only_when_not_already_paused(self):
        dispatcher, platform, _ = make()
        platform.media["playing"] = True
        dispatcher.timer._fired()
        platform.media["playing"] = False
        dispatcher.timer._fired()
        self.assertEqual(platform.calls, [("press", [], "media")])

    def test_seek_windows_and_focus_pass_through(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "seek", "to": 61.5})
        dispatcher.handle({"a": "focus", "id": 7})
        self.assertEqual(dispatcher.handle({"a": "windows"})[0]["title"], "Video")
        self.assertEqual(platform.calls, [("media_seek", 61.5), ("focus_window", 7)])

    def test_playpause_uses_system_media_control_when_possible(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "playpause"})
        self.assertEqual(platform.calls, [("media_toggle",)])

    def test_playpause_falls_back_to_space(self):
        dispatcher, platform, _ = make()
        platform.can_toggle = False
        dispatcher.handle({"a": "playpause"})
        self.assertEqual(platform.calls, [("media_toggle",), ("press", [], "space")])

    def test_track_keys_are_system_keys(self):
        dispatcher, platform, _ = make()
        dispatcher.handle({"a": "key", "k": "next"})
        dispatcher.handle({"a": "key", "k": "prev"})
        self.assertEqual(platform.calls, [("press", [], "next"), ("press", [], "prev")])

    def test_hello_reports_platform_and_features(self):
        dispatcher, _, _ = make(windows=False)
        hello = dispatcher.handle({"a": "hello"})
        self.assertEqual(hello["platform"], "win")
        self.assertFalse(hello["features"]["windows"])
        self.assertTrue(hello["features"]["touchpad"])


class FeatureSwitchTest(unittest.TestCase):
    def test_disabled_feature_blocks_its_actions(self):
        cases = {
            "touchpad": [{"a": "move"}, {"a": "click"}, {"a": "scroll"}],
            "text_input": [{"a": "text", "t": "x"}],
            "windows": [{"a": "windows"}, {"a": "focus", "id": 1}],
            "progress": [{"a": "seek", "to": 1}],
            "sleep_timer": [{"a": "timer", "min": 1}],
            "open_sites": [{"a": "open", "url": "https://example.com"}],
        }
        for feature, messages in cases.items():
            dispatcher, platform, opened = make(**{feature: False})
            for msg in messages:
                with self.subTest(feature=feature, msg=msg), self.assertRaises(FeatureDisabled):
                    dispatcher.handle(msg)
            self.assertEqual(platform.calls, [])
            self.assertEqual(opened, [])

    def test_core_keys_cannot_be_disabled(self):
        dispatcher, platform, _ = make(**dict.fromkeys(FEATURES, False))
        dispatcher.handle({"a": "key", "k": "space"})
        self.assertEqual(platform.calls, [("press", [], "space")])

    def test_state_hides_fields_of_disabled_features(self):
        full = {"playing": True, "title": "T", "pos": 12, "dur": 100, "vol": 30, "muted": True}
        dispatcher, platform, _ = make()
        platform.media = dict(full)
        self.assertEqual({k: dispatcher.handle({"a": "state"})[k] for k in full}, full)

        dispatcher, platform, _ = make(play_state=False, progress=False, volume_display=False)
        platform.media = dict(full)
        state = dispatcher.handle({"a": "state"})
        self.assertEqual((state["playing"], state["title"], state["pos"], state["dur"],
                          state["vol"], state["muted"]), (None, "", 0, 0, None, False))
        self.assertEqual(platform.media, full)  # 原始状态不能被改掉


if __name__ == "__main__":
    unittest.main()
