import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from fakes import FakePlatform
from phone_remote.actions import Dispatcher
from phone_remote.config import FEATURES
from phone_remote.server import MAX_FAILURES, make_server, sign

TOKEN = "test-token"


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.platform = FakePlatform()
        features = dict.fromkeys(FEATURES, True)
        features["windows"] = False
        dispatcher = Dispatcher(self.platform, features, opener=lambda url: None)
        self.server = make_server(0, TOKEN, dispatcher, lambda: "http://phone.example/#" + TOKEN)
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]
        self.clock = 0
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, path, body=None, token=TOKEN, sent=None, origin=None):
        data = body if isinstance(body, bytes) or body is None else json.dumps(body).encode()
        headers = {"Origin": origin} if origin else {}
        if token:
            self.clock += 1  # every command gets its own time, like the page does
            sent = str(sent or int(time.time() * 1000) + self.clock)
            headers["X-Auth"] = sent + "." + sign(token, sent, data or b"")
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

    def test_the_token_itself_is_not_accepted(self):
        request = urllib.request.Request(self.base + "/api", b'{"a": "click"}', {"X-Token": TOKEN, "X-Auth": TOKEN})
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request)
        refused.exception.close()
        self.assertEqual(refused.exception.code, 403)
        self.assertEqual(self.platform.calls, [])

    def test_signature_for_one_command_does_not_fit_another(self):
        sent = str(int(time.time() * 1000))
        headers = {"X-Auth": sent + "." + sign(TOKEN, sent, b'{"a": "ping"}')}
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(urllib.request.Request(self.base + "/api", b'{"a": "click"}', headers))
        refused.exception.close()
        self.assertEqual(refused.exception.code, 403)

    def test_overheard_command_cannot_be_replayed(self):
        sent = int(time.time() * 1000)
        self.assertEqual(self.request("/api", {"a": "click"}, sent=sent)[0], 204)
        status, body, _ = self.request("/api", {"a": "click"}, sent=sent)
        self.assertEqual(status, 401)
        self.assertAlmostEqual(json.loads(body)["now"], time.time() * 1000, delta=5000)  # lets the phone fix its clock
        self.assertEqual(len(self.platform.calls), 1)

    def test_stale_command_is_refused(self):
        for offset in (-120000, 120000):
            self.assertEqual(self.request("/api", {"a": "click"}, sent=int(time.time() * 1000) + offset)[0], 401)
        self.assertEqual(self.request("/api", {"a": "click"}, sent="soon")[0], 401)
        self.assertEqual(self.platform.calls, [])

    def test_repeated_wrong_signatures_lock_the_address_out(self):
        for _ in range(MAX_FAILURES):
            self.assertEqual(self.request("/api", {"a": "click"}, token="wrong")[0], 403)
        self.assertEqual(self.request("/api", {"a": "click"}, token="wrong")[0], 429)
        self.assertEqual(self.request("/api", {"a": "click"})[0], 429)  # even the right token has to wait
        self.assertEqual(self.platform.calls, [])

    def test_new_token_takes_over_at_once(self):
        self.server.token = "fresh-token"
        self.assertEqual(self.request("/api", {"a": "click"})[0], 403)
        self.assertEqual(self.request("/api", {"a": "click"}, token="fresh-token")[0], 204)

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

    def test_port_cannot_be_taken_twice(self):
        port = self.server.server_address[1]
        with self.assertRaises(OSError):
            make_server(port, TOKEN, None)

    def test_page_from_another_computer_may_call_the_api(self):
        peer = "http://192.168.1.5:8765"
        preflight = urllib.request.Request(self.base + "/api", method="OPTIONS", headers={"Origin": peer})
        with urllib.request.urlopen(preflight) as r:
            self.assertEqual(r.status, 204)
            self.assertEqual(r.headers["Access-Control-Allow-Origin"], peer)
            self.assertIn("X-Auth", r.headers["Access-Control-Allow-Headers"])
        sent = str(int(time.time() * 1000))
        body = json.dumps({"a": "hello"}).encode()
        request = urllib.request.Request(self.base + "/api", body,
                                         {"X-Auth": sent + "." + sign(TOKEN, sent, body), "Origin": peer})
        with urllib.request.urlopen(request) as r:
            self.assertEqual(r.headers["Access-Control-Allow-Origin"], peer)

    def test_page_from_the_internet_may_not_call_the_api(self):
        for origin in ("https://evil.example", "http://8.8.8.8", "null", ""):
            with self.subTest(origin=origin):
                preflight = urllib.request.Request(self.base + "/api", method="OPTIONS", headers={"Origin": origin})
                with urllib.request.urlopen(preflight) as r:
                    self.assertIsNone(r.headers["Access-Control-Allow-Origin"])

    def test_only_api_accepts_posts(self):
        self.assertEqual(self.request("/other", {"a": "ping"})[0], 404)


if __name__ == "__main__":
    unittest.main()
