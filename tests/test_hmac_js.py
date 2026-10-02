import hashlib
import hmac
import json
import shutil
import subprocess
import unittest
from pathlib import Path

HMAC_JS = Path(__file__).parent.parent / "src" / "phone_remote" / "web" / "js" / "hmac.js"
# Lengths around the 55/56 and 64 byte padding boundaries, a long key, and text that is not ASCII
CASES = [("key", ""), ("a2743758178f5f61", "1790880000000\n" + json.dumps({"a": "move", "dx": 3, "dy": -4})),
         ("k", "x" * 55), ("k", "x" * 56), ("k", "x" * 63), ("k", "x" * 64), ("k", "x" * 65), ("k", "x" * 5000),
         ("K" * 100, "long key"), ("钥匙", "中文和 emoji 😀")]


@unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
class HmacJsTest(unittest.TestCase):
    def test_page_signs_the_same_way_as_the_server(self):
        # The file is an ES module; feeding it on stdin with the calls appended avoids needing a package.json
        script = (HMAC_JS.read_text(encoding="utf-8").replace("export function", "function")
                  + "\nconsole.log(JSON.stringify(%s.map(([k, m]) => hmacSha256(k, m))));" % json.dumps(CASES))
        result = subprocess.run(["node", "--input-type=module", "-"], input=script.encode("utf-8"),
                                capture_output=True, check=True)
        expected = [hmac.new(k.encode(), m.encode(), hashlib.sha256).hexdigest() for k, m in CASES]
        self.assertEqual(json.loads(result.stdout), expected)


if __name__ == "__main__":
    unittest.main()
