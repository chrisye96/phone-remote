import unittest

from phone_remote import pairing


class PairPageTest(unittest.TestCase):
    URL = "http://192.168.1.5:8765/#abc123"

    def test_shows_the_url_and_a_qr_code(self):
        page = pairing.pair_page(self.URL)
        self.assertIn(self.URL, page)
        self.assertTrue("<svg" in page or "qrcode" in page)

    def test_hint_matches_how_the_program_runs(self):
        self.assertIn("托盘", pairing.pair_page(self.URL, tray_mode=True))
        self.assertIn("命令行窗口", pairing.pair_page(self.URL, tray_mode=False))

    def test_url_is_escaped(self):
        page = pairing.pair_page('http://x/#"><script>alert(1)</script>')
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_phone_url_has_port_and_token(self):
        self.assertRegex(pairing.phone_url(8765, "tok"), r"^http://[\d.]+:8765/#tok$")


if __name__ == "__main__":
    unittest.main()
