import sys
import unittest

from phone_remote import autostart


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


if __name__ == "__main__":
    unittest.main()
