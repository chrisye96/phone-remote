import unittest

from phone_remote import update


def answers(tag):
    return lambda: {"tag_name": tag}


class UpdateCheckTest(unittest.TestCase):
    def test_reports_only_a_release_newer_than_the_running_one(self):
        self.assertEqual(update.newer_version("0.4.1", answers("v0.5.0")), "0.5.0")
        self.assertEqual(update.newer_version("0.4.1", answers("v0.4.2")), "0.4.2")
        self.assertEqual(update.newer_version("0.9.0", answers("v0.10.0")), "0.10.0")  # numbers, not text
        self.assertIsNone(update.newer_version("0.4.1", answers("v0.4.1")))
        self.assertIsNone(update.newer_version("0.5.0", answers("v0.4.9")))

    def test_any_failure_means_nothing_to_report(self):
        def offline():
            raise OSError("no network")
        self.assertIsNone(update.newer_version("0.4.1", offline))
        self.assertIsNone(update.newer_version("0.4.1", lambda: {"message": "rate limited"}))
        self.assertIsNone(update.newer_version("0.4.1", lambda: "not json"))

    def test_only_plain_version_numbers_are_accepted(self):
        # The text ends up in the tray menu, so nothing but digits and dots may come through
        for tag in ("v9.9.9-beta", "latest", "9.9.9; rm -rf", "<b>9.9.9</b>", "", None):
            with self.subTest(tag=tag):
                self.assertIsNone(update.newer_version("0.4.1", answers(tag)))

    def test_download_page_is_fixed_and_on_github(self):
        self.assertTrue(update.RELEASES_PAGE.startswith("https://github.com/chrisye96/phone-remote/"))


if __name__ == "__main__":
    unittest.main()
