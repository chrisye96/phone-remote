import unittest

from phone_remote.keys import KEYS, parse_combo


class ParseComboTest(unittest.TestCase):
    def test_plain_key(self):
        self.assertEqual(parse_combo("space"), ([], "space"))

    def test_modifiers_are_split_off(self):
        self.assertEqual(parse_combo("ctrl+shift+tab"), (["ctrl", "shift"], "tab"))

    def test_case_is_ignored(self):
        self.assertEqual(parse_combo("Mod+L"), (["mod"], "l"))

    def test_punctuation_keys(self):
        self.assertEqual(parse_combo("shift+,"), (["shift"], ","))
        self.assertEqual(parse_combo("mod+="), (["mod"], "="))

    def test_system_keys_take_no_modifiers(self):
        self.assertEqual(parse_combo("volup"), ([], "volup"))
        with self.assertRaises(ValueError):
            parse_combo("ctrl+volup")

    def test_unknown_key_or_modifier_is_rejected(self):
        for bad in ("zzz", "foo+a", "", "ctrl+", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_combo(bad)

    def test_every_key_has_both_platform_codes(self):
        for name, codes in KEYS.items():
            self.assertEqual(len(codes), 2, name)


if __name__ == "__main__":
    unittest.main()
