import json
import re
import shutil
import subprocess
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

    def test_computers_own_language_is_used_when_there_is_a_table_for_it(self):
        # What Windows and macOS report: zh_CN, zh_TW, zh-Hans_US, en_US, ...
        for name, code in (("zh_CN", "zh"), ("zh_TW", "zh"), ("zh-Hans_US", "zh"), ("ZH_cn\n", "zh"),
                           ("en_US", "en"), ("fr_FR", "en"), ("", "en"), (None, "en")):
            with self.subTest(name=name):
                self.assertEqual(i18n._supported(name), code)
        self.assertIn(i18n.system_language(), i18n.LANGUAGES)  # asks this computer for real; must not raise

    @unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
    def test_phone_page_starts_in_the_phones_own_language_until_one_is_chosen(self):
        # [chosen in Settings, the phone's language] -> language the page comes up in
        cases = [([None, "zh-CN"], "zh"), ([None, "zh-TW"], "zh"), ([None, "en-US"], "en"), ([None, "fr-FR"], "en"),
                 (["en", "zh-CN"], "en"), (["zh", "en-US"], "zh"), (["klingon", "zh-CN"], "en"), ([None, None], "en")]
        module = (WEB / "js" / "i18n.js").read_text(encoding="utf-8")
        module = re.sub(r"^import .*$", "", module, flags=re.M).replace("export ", "")
        script = ("function resolve(stored, language) { const navigator = { language }, store = { get: () => stored };\n"
                  + module + "\nreturn lang; }\n"
                  "console.log(JSON.stringify(%s.map(c => resolve(...c))));" % json.dumps([c for c, _ in cases]))
        result = subprocess.run(["node", "--input-type=module", "-"], input=script.encode("utf-8"),
                                capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [lang for _, lang in cases])

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
        self.assertEqual(re.findall(r"[一-鿿]+", page), ["中文"])  # only the language's own name, in Settings


if __name__ == "__main__":
    unittest.main()
