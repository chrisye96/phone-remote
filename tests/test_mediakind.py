import unittest

from phone_remote.mediakind import classify


class ClassifyTest(unittest.TestCase):
    def test_known_apps_decide_the_kind(self):
        # The first two ids are what Windows reported for real sessions
        self.assertEqual(classify("SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify"), ("music", "Spotify"))
        self.assertEqual(classify("foobar2000.exe", "蔡琴"), ("music", "foobar2000"))
        self.assertEqual(classify("C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"), ("video", "VLC"))

    def test_in_a_browser_an_album_means_music(self):
        self.assertEqual(classify("Chrome", "Some channel"), ("video", "Chrome"))
        self.assertEqual(classify("MSEdge", "Artist", "Album"), ("music", "Edge"))

    def test_unknown_apps_get_a_readable_name_and_a_guess_from_the_metadata(self):
        self.assertEqual(classify("SomePlayer.exe"), ("", "SomePlayer"))
        self.assertEqual(classify("Vendor.App_abc123!Player", "Artist"), ("music", "Player"))
        self.assertEqual(classify(None), ("", ""))


if __name__ == "__main__":
    unittest.main()
