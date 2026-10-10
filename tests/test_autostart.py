import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from phone_remote import autostart

if sys.platform == "win32":
    import winreg


class LaunchCommandTest(unittest.TestCase):
    def test_runs_in_background_without_the_pair_page(self):
        command = autostart.launch_command()
        self.assertEqual(command[-1], "--background")
        self.assertIn("phone_remote", command)


@unittest.skipUnless(sys.platform == "win32", "Windows 注册表")
class WindowsAutostartTest(unittest.TestCase):
    NAME = "PhoneRemoteSelfTest"  # 用单独的名字，不碰真正的开关

    def tearDown(self):
        autostart.set_enabled(False, self.NAME)

    def test_toggle(self):
        self.assertFalse(autostart.is_enabled(self.NAME))
        autostart.set_enabled(True, self.NAME)
        self.assertTrue(autostart.is_enabled(self.NAME))
        autostart.set_enabled(False, self.NAME)
        self.assertFalse(autostart.is_enabled(self.NAME))
        autostart.set_enabled(False, self.NAME)  # 已经关着时再关不报错

    def write(self, command):
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, autostart.RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, self.NAME, 0, winreg.REG_SZ, command)

    def read(self):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, autostart.RUN_KEY) as key:
            return winreg.QueryValueEx(key, self.NAME)[0]

    def test_an_entry_left_by_another_copy_does_not_count_and_one_click_takes_it_over(self):
        # After an update saved under a new name, the entry still starts the old file
        self.write(r'"C:\Old place\PhoneRemote.exe" --background')
        self.assertFalse(autostart.is_enabled(self.NAME))
        autostart.set_enabled(not autostart.is_enabled(self.NAME), self.NAME)  # what the tray menu does
        self.assertTrue(autostart.is_enabled(self.NAME))
        self.assertEqual(self.read(), subprocess.list2cmdline(autostart.launch_command()))

    def test_the_same_path_in_other_letter_case_is_still_this_copy(self):
        self.write(subprocess.list2cmdline(autostart.launch_command()).upper())
        self.assertTrue(autostart.is_enabled(self.NAME))

    def test_an_entry_left_by_another_copy_can_still_be_switched_off(self):
        self.write(r'"C:\Old place\PhoneRemote.exe" --background')
        autostart.set_enabled(False, self.NAME)
        with self.assertRaises(OSError):
            self.read()


@unittest.skipIf(sys.platform == "win32", "macOS LaunchAgent")
class MacAutostartTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.plist = Path(folder.name) / "LaunchAgents" / "test.plist"  # not the real one
        patcher = mock.patch.object(autostart, "_plist_path", return_value=self.plist)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_toggle(self):
        self.assertFalse(autostart.is_enabled())
        autostart.set_enabled(True)
        self.assertTrue(autostart.is_enabled())
        autostart.set_enabled(False)
        self.assertFalse(autostart.is_enabled())
        autostart.set_enabled(False)

    def test_an_entry_left_by_another_copy_does_not_count_and_one_click_takes_it_over(self):
        self.plist.parent.mkdir(parents=True)
        with open(self.plist, "wb") as f:
            plistlib.dump({"Label": "x", "ProgramArguments": ["/Old place/PhoneRemote", "--background"]}, f)
        self.assertFalse(autostart.is_enabled())
        autostart.set_enabled(not autostart.is_enabled())
        self.assertTrue(autostart.is_enabled())
        with open(self.plist, "rb") as f:
            self.assertEqual(plistlib.load(f)["ProgramArguments"], autostart.launch_command())

    def test_a_file_that_cannot_be_read_counts_as_off(self):
        self.plist.parent.mkdir(parents=True)
        self.plist.write_text("not a plist", encoding="utf-8")
        self.assertFalse(autostart.is_enabled())
        autostart.set_enabled(False)
        self.assertFalse(self.plist.exists())


if __name__ == "__main__":
    unittest.main()
