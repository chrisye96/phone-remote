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

    def test_broken_config_file_falls_back_to_defaults(self):
        self.data.mkdir()
        (self.data / "config.json").write_text("{not json", encoding="utf-8")
        self.assertTrue(all(config.load().features.values()))

    def test_environment_port_wins(self):
        with mock.patch.dict(os.environ, {"REMOTE_PORT": "8766"}):
            self.assertEqual(config.load().port, 8766)


if __name__ == "__main__":
    unittest.main()
