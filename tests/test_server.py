import json
import threading
import unittest
import urllib.error
import urllib.request

from fakes import FakePlatform
from phone_remote.actions import Dispatcher
from phone_remote.config import FEATURES
from phone_remote.server import make_server

TOKEN = "test-token"


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.platform = FakePlatform()
        features = dict.fromkeys(FEATURES, True)
        features["windows"] = False
        dispatcher = Dispatcher(self.platform, features, opener=lambda url: None)
        self.server = make_server(0, TOKEN, dispatcher, "http://phone.example/#" + TOKEN)
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, path, body=None, token=TOKEN):
        headers = {"X-Token": token} if token else {}
        data = body if isinstance(body, bytes) or body is None else json.dumps(body).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(self.base + path, data, headers)) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read(), ""

    def test_command_runs_with_the_right_token(self):
        self.assertEqual(self.request("/api", {"a": "key", "k": "space"})[0], 204)
        self.assertEqual(self.platform.calls, [("press", [], "space")])

    def test_wrong_or_missing_token_is_refused(self):
        self.assertEqual(self.request("/api", {"a": "click"}, token="wrong")[0], 403)
        self.assertEqual(self.request("/api", {"a": "click"}, token=None)[0], 403)
        self.assertEqual(self.platform.calls, [])

    def test_bad_requests_get_400(self):
        self.assertEqual(self.request("/api", b"not json")[0], 400)
        self.assertEqual(self.request("/api", {"a": "key", "k": "zzz"})[0], 400)
        self.assertEqual(self.request("/api", ["list"])[0], 400)
        self.assertEqual(self.request("/api", b"x" * 20000)[0], 400)

    def test_disabled_feature_gets_423(self):
        self.assertEqual(self.request("/api", {"a": "windows"})[0], 423)

    def test_results_come_back_as_json(self):
        status, body, content_type = self.request("/api", {"a": "hello"})
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(json.loads(body)["platform"], "win")

    def test_page_and_assets_are_served(self):
        status, body, content_type = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"js/main.js", body)
        self.assertIn("javascript", self.request("/js/main.js")[2])
        self.assertIn("text/css", self.request("/css/app.css")[2])

    def test_files_outside_the_web_folder_are_not_served(self):
        for path in ("/../server.py", "/js/../../server.py", "/..%2fserver.py", "/media_helper.ps1",
                     "/js/missing.js", "/js"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_pair_page_shows_the_phone_url_to_this_computer(self):
        status, body, _ = self.request("/pair")
        self.assertEqual(status, 200)
        self.assertIn(b"http://phone.example/#" + TOKEN.encode(), body)

    def test_only_api_accepts_posts(self):
        self.assertEqual(self.request("/other", {"a": "ping"})[0], 404)


if __name__ == "__main__":
    unittest.main()
