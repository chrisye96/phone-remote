import re
import unittest
from pathlib import Path

from phone_remote import i18n

SOURCE = Path(__file__).parent.parent / "src" / "phone_remote"
WEB = SOURCE / "web"


class TranslationTest(unittest.TestCase):
    def test_unknown_language_and_unknown_text_fall_back_to_english(self):
        self.addCleanup(i18n.set_language, i18n.DEFAULT)
        i18n.set_language("zh")
        self.assertEqual(i18n.t("Quit"), "退出")
        self.assertEqual(i18n.t("not in the table"), "not in the table")
        i18n.set_language("klingon")
        self.assertEqual(i18n.t("Quit"), "Quit")

    def test_every_translated_text_is_still_used_by_the_program(self):
        # A table entry whose English text was reworded in the code would silently stop translating
        code = "".join(p.read_text(encoding="utf-8") for p in SOURCE.rglob("*.py") if p.name != "i18n.py")
        code = re.sub(r'"\s*\n\s*"', "", code)  # join strings split across lines
        for text in i18n._TABLES["zh"]:
            with self.subTest(text=text):
                self.assertTrue(text in code or any(part in code for part in (text[:60], text[-40:])), text)

    def test_every_translated_text_is_still_on_the_phone_page(self):
        table = (WEB / "js" / "i18n.js").read_text(encoding="utf-8")
        keys = re.findall(r'^\s+"((?:[^"\\]|\\.)+)":', table, re.M)
        self.assertGreater(len(keys), 100)
        page = (WEB / "index.html").read_text(encoding="utf-8")
        page += "".join(p.read_text(encoding="utf-8") for p in (WEB / "js").glob("*.js") if p.name != "i18n.js")
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key.replace("'", "\\'") if key.replace("'", "\\'") in page else key, page)

    def test_phone_page_has_no_untranslated_chinese_left_in_it(self):
        page = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"[一-鿿]+", page), ["中"])  # only the language switch itself


if __name__ == "__main__":
    unittest.main()
