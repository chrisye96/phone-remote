import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from phone_remote import config


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.data = Path(self.folder.name) / "data"
        cwd = os.getcwd()
        os.chdir(self.folder.name)  # 旧版配对码是从当前目录找的
        self.addCleanup(os.chdir, cwd)
        patcher = mock.patch.dict(os.environ, {"REMOTE_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("REMOTE_PORT", None)

    def test_first_run_creates_token_and_config(self):
        loaded = config.load()
        self.assertEqual(len(loaded.token), 16)
        self.assertEqual(loaded.port, config.DEFAULT_PORT)
        self.assertTrue(all(loaded.features.values()))
        saved = json.loads((self.data / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(set(saved["features"]), set(config.FEATURES))

    def test_token_stays_the_same_between_runs(self):
        self.assertEqual(config.load().token, config.load().token)

    def test_legacy_token_next_to_the_program_is_adopted(self):
        Path("token.txt").write_text("oldtoken12345678", encoding="utf-8")
        self.assertEqual(config.load().token, "oldtoken12345678")
        self.assertEqual((self.data / "token.txt").read_text(encoding="utf-8"), "oldtoken12345678")

    def test_feature_switches_and_port_are_read_back(self):
        self.data.mkdir()
        (self.data / "config.json").write_text(
            json.dumps({"port": 9000, "features": {"windows": False, "made_up": False}}),
            encoding="utf-8")
        loaded = config.load()
        self.assertEqual(loaded.port, 9000)
        self.assertFalse(loaded.features["windows"])
        self.assertTrue(loaded.features["touchpad"])
        self.assertNotIn("made_up", loaded.features)

    def test_shortcuts_have_defaults_and_are_saved(self):
        loaded = config.load()
        self.assertEqual([s["name"] for s in loaded.shortcuts], ["B站", "YouTube"])
        loaded.shortcuts.append({"name": "爱壹帆", "url": "https://example.com", "color": "#112233"})
        config.save(loaded)
        self.assertEqual(config.load().shortcuts[2]["name"], "爱壹帆")

    def test_bad_shortcuts_in_the_file_are_dropped(self):
        self.data.mkdir()
        entries = [{"name": "ok", "url": "https://ok.example"}, {"name": "bad", "url": "javascript:x"}, "junk"]
        entries += [{"name": str(n), "url": "https://%d.example" % n} for n in range(6)]
        (self.data / "config.json").write_text(json.dumps({"shortcuts": entries}), encoding="utf-8")
        loaded = config.load()
        self.assertEqual(len(loaded.shortcuts), config.MAX_SHORTCUTS)
        self.assertEqual(loaded.shortcuts[0]["name"], "ok")
        self.assertNotIn("bad", [s["name"] for s in loaded.shortcuts])

    def test_environment_port_is_not_written_to_the_file(self):
        with mock.patch.dict(os.environ, {"REMOTE_PORT": "8766"}):
            config.save(config.load())
        self.assertEqual(config.load().port, config.DEFAULT_PORT)

    def test_broken_config_file_falls_back_to_defaults(self):
        self.data.mkdir()
        (self.data / "config.json").write_text("{not json", encoding="utf-8")
        self.assertTrue(all(config.load().features.values()))

    def test_environment_port_wins(self):
        with mock.patch.dict(os.environ, {"REMOTE_PORT": "8766"}):
            self.assertEqual(config.load().port, 8766)


if __name__ == "__main__":
    unittest.main()
