import unittest

from phone_remote import i18n, pairing


class PairPageTest(unittest.TestCase):
    URL = "http://192.168.1.5:8765/#abc123"

    def test_shows_the_url_and_a_qr_code(self):
        page = pairing.pair_page(self.URL)
        self.assertIn(self.URL, page)
        self.assertTrue("<svg" in page or "qrcode" in page)

    def test_hint_matches_how_the_program_runs(self):
        self.assertIn("Re-pair in the tray menu", pairing.pair_page(self.URL, tray_mode=True))
        self.assertIn("terminal window", pairing.pair_page(self.URL, tray_mode=False))

    def test_page_follows_the_chosen_language(self):
        self.assertIn("Scan with your phone", pairing.pair_page(self.URL))
        i18n.set_language("zh")
        self.addCleanup(i18n.set_language, i18n.DEFAULT)
        page = pairing.pair_page(self.URL, tray_mode=True)
        self.assertIn("用手机相机扫码", page)
        self.assertIn("重新配对", page)
        self.assertIn('lang="zh"', page)
        self.assertNotRegex(page, r"__[A-Z]+__")  # every mark in the template was filled in

    def test_address_can_be_copied_with_one_click(self):
        page = pairing.pair_page(self.URL)
        self.assertIn('id="copy"', page)
        self.assertIn("/js/pair.js", page)
        self.assertIn("icons.svg#copy", page)

    def test_url_is_escaped(self):
        page = pairing.pair_page('http://x/#"><script>alert(1)</script>')
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_phone_url_has_port_and_token(self):
        self.assertRegex(pairing.phone_url(8765, "tok"), r"^http://[\d.]+:8765/#tok$")


if __name__ == "__main__":
    unittest.main()
