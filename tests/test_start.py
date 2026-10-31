"""What starting does when the port cannot be had: who is told what, and whether the QR page opens."""
import contextlib
import errno
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fakes import FakePlatform
from phone_remote import __main__ as app
from phone_remote import i18n
from phone_remote.server import make_server

PORT = 8765
# What the socket raises on a port Windows has reserved (WinError 10013, seen for real on 8765)
REFUSED = PermissionError(errno.EACCES, "forbidden by its access permissions")


class PortFailureTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.addCleanup(i18n.set_language, i18n.DEFAULT)
        self.config_file = Path(folder.name) / "config.json"
        self.platform = FakePlatform()
        for patcher in (mock.patch.dict(os.environ, {"REMOTE_DATA_DIR": folder.name}),
                        mock.patch.object(app, "get_platform", return_value=self.platform),
                        mock.patch.object(app.logging, "basicConfig")):  # a log file would stay open in the folder
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(app.webbrowser, "open")
        self.opened = patcher.start()
        self.addCleanup(patcher.stop)

    def start(self, port, *flags):
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"REMOTE_PORT": str(port)}), \
                mock.patch.object(sys, "argv", ["phone_remote", *flags]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            app.main()
        return output.getvalue()

    def start_refused(self, *flags):
        with mock.patch("socketserver.TCPServer.server_bind", side_effect=REFUSED):
            return self.start(PORT, *flags)

    def taken_port(self):
        holder = make_server(0, "token", None)
        self.addCleanup(holder.server_close)
        return holder.server_address[1]

    def test_port_in_use_opens_the_page_of_the_copy_already_running(self):
        port = self.taken_port()
        output = self.start(port, "--console")
        self.assertIn("Port %d is already in use" % port, output)
        self.opened.assert_called_once_with("http://127.0.0.1:%d/pair" % port)
        self.assertEqual(self.platform.calls, [])

    def test_port_in_use_stays_silent_when_started_at_login(self):
        self.start(self.taken_port(), "--background")
        self.opened.assert_not_called()
        self.assertEqual(self.platform.calls, [])

    def test_refused_port_says_what_is_wrong_and_how_to_change_it(self):
        output = self.start_refused("--console")
        self.assertIn("Port %d is blocked or reserved" % PORT, output)
        self.assertIn(str(self.config_file), output)
        self.assertNotIn("already", output)  # no other copy exists, so nothing may suggest one does
        self.assertEqual(self.platform.calls, [])  # the terminal shows it; no dialog on top of that

    def test_refused_port_opens_no_qr_page_because_nothing_serves_it(self):
        for flags in ((), ("--console",)):
            with self.subTest(flags=flags):
                self.start_refused(*flags)
                self.opened.assert_not_called()

    def test_refused_port_reaches_someone_with_no_terminal(self):
        # The packaged app has no console, so what print says goes nowhere. The ranges Windows reserves
        # change at a reboot, so a start at login is when this is most likely: it is told then as well.
        for flags in ((), ("--background",)):
            with self.subTest(flags=flags):
                self.platform.calls.clear()
                self.start_refused(*flags)
                (call, title, text), = self.platform.calls
                self.assertEqual((call, title), ("show_error", "Phone Remote"))
                self.assertIn("Port %d is blocked or reserved" % PORT, text)
                self.assertIn(str(self.config_file), text)
                self.assertNotIn("already", text)

    def test_refused_port_is_explained_in_the_chosen_language(self):
        self.config_file.write_text(json.dumps({"language": "zh"}), encoding="utf-8")
        self.start_refused()
        (_, title, text), = self.platform.calls
        self.assertEqual(title, "手机遥控器")
        self.assertIn("端口 %d" % PORT, text)
        self.assertIn(str(self.config_file), text)
        self.assertNotIn("Port", text)


@unittest.skipUnless(sys.platform == "darwin", "macOS only: the package loads system frameworks")
class MacErrorDialogTest(unittest.TestCase):
    def test_text_travels_as_arguments_so_quotes_in_it_cannot_break_the_script(self):
        from phone_remote.platforms.macos import script
        with mock.patch.object(script.subprocess, "Popen") as popen:
            script.show_error('Title', 'A "quoted" path')
        command = popen.call_args.args[0]
        self.assertEqual(command[-2:], ["Title", 'A "quoted" path'])
        self.assertEqual(command[0], "osascript")
        self.assertNotIn("quoted", " ".join(command[:-2]))


if __name__ == "__main__":
    unittest.main()
