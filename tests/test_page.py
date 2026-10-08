"""The phone page for people who do not use it by touch and sight: screen readers, keyboards, switches."""
import base64
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

WEB = Path(__file__).parent.parent / "src" / "phone_remote" / "web"

# Each case is the events one button receives, as [type, time in ms], and how often it should act
PRESS_CASES = [
    ([["pointerdown", 0], ["pointerup", 90], ["click", 95]], 1),             # a tap acts once, on the way down
    ([["pointerdown", 0], ["pointerup", 5000], ["click", 5004]], 1),         # so does a long hold
    ([["click", 0]], 1),                                                     # keyboard, switch or screen reader
    ([["pointerdown", 0], ["click", 9000]], 2),                              # finger slid off, later a keyboard click
    ([["click", 0], ["click", 40]], 2),                                      # Enter held down on a repeating key
]


class PageTest(unittest.TestCase):
    def test_every_button_has_a_name_a_screen_reader_can_say(self):
        page = (WEB / "index.html").read_text(encoding="utf-8")
        buttons = re.findall(r"<button\b([^>]*)>(.*?)</button>", page, re.S)
        self.assertGreater(len(buttons), 80)
        for attributes, inside in buttons:
            with self.subTest(button=attributes.strip()):
                self.assertTrue("aria-label=" in attributes or re.sub(r"<[^>]+>", "", inside).strip())

    @unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
    def test_a_button_acts_once_however_it_is_pressed(self):
        script = ((WEB / "js" / "press.js").read_text(encoding="utf-8").replace("export function", "function") + """
const counts = %s.map(events => {
  const listeners = {}, element = { addEventListener(type, fn) { listeners[type] = fn; } };
  let count = 0;
  onPress(element, () => count++);
  events.forEach(([type, timeStamp]) => listeners[type]({ type, timeStamp }));
  return count;
});
console.log(JSON.stringify(counts));""" % json.dumps([events for events, _ in PRESS_CASES]))
        result = subprocess.run(["node", "--input-type=module", "-"], input=script.encode("utf-8"),
                                capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [count for _, count in PRESS_CASES])

    @unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
    def test_bundled_reader_reads_the_qr_code_the_computer_shows(self):
        # Adding a computer from a photo depends on web/vendor/jsQR.js understanding what pairing.py draws
        import io

        import segno
        from PIL import Image

        from phone_remote.pairing import phone_url

        url = phone_url(8765, "0123456789abcdef0123456789abcdef")
        drawn = io.BytesIO()
        segno.make(url, error="m").save(drawn, kind="png", scale=6, border=4)
        image = Image.open(drawn).convert("RGBA").rotate(7, expand=True, fillcolor="white")  # held a little crooked
        script = ((WEB / "vendor" / "jsQR.js").read_text(encoding="utf-8") + """
const pixels = new Uint8ClampedArray(Buffer.from(%s, "base64"));
const found = module.exports(pixels, %d, %d);
console.log(JSON.stringify(found && found.data));""" % (json.dumps(base64.b64encode(image.tobytes()).decode()), *image.size))
        result = subprocess.run(["node", "-"], input=script.encode("utf-8"), capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), url)


if __name__ == "__main__":
    unittest.main()
