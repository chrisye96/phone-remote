"""Moving the phone from the computer's IP address to its name, which stays the same when the router changes the IP."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

WEB = Path(__file__).parent.parent / "src" / "phone_remote" / "web"
HERE = "http://10.0.0.177:8765"
NAME = "http://dianna.local:8765"
ME = {"url": HERE, "token": "tok", "name": "Dianna", "alias": "Living room"}
OTHER = {"url": "http://10.0.0.50:8765", "token": "other"}


def module(name):
    """A page script without its imports, so a test can hand it stand-ins for them."""
    source = (WEB / "js" / name).read_text(encoding="utf-8")
    return re.sub(r"^import .*$", "", source, flags=re.M).replace("export ", "")


def run(script):
    result = subprocess.run(["node", "--input-type=module", "-"], input=script.encode("utf-8"),
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def settle(origin=HERE, local="dianna.local", answers=True, standalone=False, device=ME, devices=None, stored=None):
    """Runs one page load's decision and reports what the page did."""
    setup = {"origin": origin, "local": local, "answers": answers, "standalone": standalone, "active": device,
             "devices": devices or [device], "stored": stored or {}}
    return run("const setup = %s;\n" % json.dumps(setup) + """
const report = { probed: [], moved: null, replaced: null, opened: false, link: null };
const devices = setup.devices, active = devices.find(d => d.url === setup.active.url), token = active.token;
const location = { origin: setup.origin, replace(url) { report.replaced = url; } };
const navigator = { standalone: setup.standalone };
const matchMedia = () => ({ matches: false });
const stored = setup.stored;
const store = { get: k => (k in stored ? stored[k] : null), set(k, v) { stored[k] = v; }, all: () => ({ ...stored }) };
const proves = url => { report.probed.push(url); return Promise.resolve(setup.answers); };
const moveActive = url => { report.moved = url; };
const renderDevices = () => {};
const button = () => ({ addEventListener() {} });
const elements = { stablesheet: { hidden: true }, stablelink: button(), stablelater: button() };
const document = { getElementById: id => elements[id] };
""" + module("stable.js") + """
await settleAddress(setup.local);
report.opened = !elements.stablesheet.hidden;
report.link = elements.stablelink.href || null;
report.hinted = stored.stablehint || null;
console.log(JSON.stringify(report));""")


@unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
class SettleAddressTest(unittest.TestCase):
    def carried(self, url):
        text = re.search(r"&carry=(.*)$", url).group(1)
        return run("console.log(decodeURIComponent(%s))" % json.dumps(text))

    def test_a_browser_tab_moves_to_the_name_before_an_icon_gets_added(self):
        report = settle(stored={"side": "left"})
        self.assertEqual(report["probed"], [NAME])
        self.assertTrue(report["replaced"].startswith(NAME + "/#tok&carry="))
        self.assertFalse(report["opened"])

    def test_settings_come_along_under_the_new_address(self):
        report = settle(stored={"side": "left", "active": HERE, "devices": "ignored"}, devices=[ME, OTHER])
        carried = self.carried(report["replaced"])
        self.assertEqual(carried["side"], "left")
        self.assertEqual(carried["active"], NAME)
        self.assertEqual(json.loads(carried["devices"]), [dict(ME, url=NAME), OTHER])

    def test_the_old_entry_does_not_stay_beside_the_new_one(self):
        report = settle(devices=[ME, {"url": NAME, "token": "old"}])
        self.assertEqual(json.loads(self.carried(report["replaced"])["devices"]), [dict(ME, url=NAME)])

    def test_stays_on_the_ip_when_the_name_does_not_answer(self):
        report = settle(answers=False)
        self.assertEqual(report["probed"], [NAME])
        self.assertIsNone(report["replaced"])
        self.assertIsNone(report["moved"])
        self.assertFalse(report["opened"])

    def test_nothing_happens_without_a_usable_name(self):
        report = settle(local="")
        self.assertEqual(report["probed"], [])

    def test_nothing_happens_once_on_the_name(self):
        report = settle(origin=NAME, device=dict(ME, url=NAME))
        self.assertEqual(report["probed"], [])

    def test_a_page_on_the_computer_itself_stays_put(self):
        loopback = "http://127.0.0.1:8765"
        report = settle(origin=loopback, device=dict(ME, url=loopback))
        self.assertEqual(report["probed"], [])

    def test_an_old_icon_asks_once_because_a_page_cannot_change_it(self):
        report = settle(standalone=True, stored={"side": "left"})
        self.assertIsNone(report["replaced"])
        self.assertTrue(report["opened"])
        self.assertEqual(report["hinted"], "1")
        self.assertTrue(report["link"].startswith(NAME + "/#tok&carry="))
        self.assertEqual(self.carried(report["link"])["side"], "left")

    def test_an_old_icon_is_not_asked_twice(self):
        report = settle(standalone=True, stored={"stablehint": "1"})
        self.assertEqual(report["probed"], [])
        self.assertFalse(report["opened"])

    def test_no_hint_when_an_old_icon_cannot_reach_the_name(self):
        report = settle(standalone=True, answers=False)
        self.assertFalse(report["opened"])
        self.assertIsNone(report["hinted"])

    def test_another_paired_computer_is_updated_in_place(self):
        report = settle(device=OTHER, devices=[ME, OTHER], local="living-room.local")
        self.assertEqual(report["moved"], "http://living-room.local:8765")
        self.assertIsNone(report["replaced"])
        self.assertFalse(report["opened"])


@unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
class ProvesTest(unittest.TestCase):
    def proves(self, answer):
        """answer is JavaScript for what the computer says back, given the value the phone asked it to sign."""
        source = module("api.js").replace("PROVE_TIMEOUT = 3000", "PROVE_TIMEOUT = 20")
        return run("""
const stored = { devices: JSON.stringify([{ url: "http://10.0.0.177:8765", token: "tok" }]), active: "http://10.0.0.177:8765" };
const store = { get: k => (k in stored ? stored[k] : null), set(k, v) { stored[k] = v; } };
const location = { href: "http://10.0.0.177:8765/", origin: "http://10.0.0.177:8765" };
const hmacSha256 = (key, text) => key + "|" + text, t = text => text, setStatus = () => {};
const requests = [];
const fetch = (url, options) => { requests.push(url); const value = options.body; return %s; };
""" % answer + source + """
const result = await proves("http://dianna.local:8765");
console.log(JSON.stringify({ result, requests }));""")

    def test_right_proof_passes(self):
        report = self.proves('Promise.resolve({ ok: true, text: () => Promise.resolve("tok|prove\\n" + value) })')
        self.assertEqual(report, {"result": True, "requests": ["http://dianna.local:8765/prove"]})

    def test_proof_for_another_value_fails(self):
        report = self.proves('Promise.resolve({ ok: true, text: () => Promise.resolve("tok|prove\\nsomething else") })')
        self.assertFalse(report["result"])

    def test_refusal_fails(self):
        self.assertFalse(self.proves('Promise.resolve({ ok: false, text: () => Promise.resolve("") })')["result"])

    def test_no_connection_fails(self):
        self.assertFalse(self.proves('Promise.reject(new TypeError("no route"))')["result"])

    def test_no_answer_in_time_fails(self):
        self.assertFalse(self.proves("new Promise(() => {})")["result"])

    def test_moving_a_computer_replaces_its_old_address(self):
        result = run("""
const stored = { devices: JSON.stringify([{ url: "http://10.0.0.50:8765", token: "tok", alias: "Bedroom" },
                                          { url: "http://bedroom.local:8765", token: "old" }]),
                 active: "http://10.0.0.50:8765" };
const store = { get: k => (k in stored ? stored[k] : null), set(k, v) { stored[k] = v; } };
const location = { href: "http://10.0.0.177:8765/", origin: "http://10.0.0.177:8765" };
const hmacSha256 = () => "", t = text => text, setStatus = () => {};
""" + module("api.js") + """
moveActive("http://bedroom.local:8765");
console.log(JSON.stringify({ devices: JSON.parse(stored.devices), active: stored.active }));""")
        self.assertEqual(result, {"devices": [{"url": "http://bedroom.local:8765", "token": "tok", "alias": "Bedroom"}],
                                  "active": "http://bedroom.local:8765"})


@unittest.skipUnless(shutil.which("node"), "needs Node.js to run the page's JavaScript")
class ArrivalTest(unittest.TestCase):
    def arrive(self, hash_, stored=None):
        setup = {"hash": hash_, "stored": stored or {}}
        return run("const setup = %s;\n" % json.dumps(setup) + """
const location = { hash: setup.hash }, report = { url: null };
const history = { replaceState(state, title, url) { report.url = url; location.hash = url; } };
const values = setup.stored;
const localStorage = new Proxy(values, {
  get(target, key) {
    if (key === "getItem") return k => (k in target ? target[k] : null);
    if (key === "setItem") return (k, v) => { target[k] = String(v); };
    return target[key];
  },
});
""" + module("store.js") + """
report.stored = values;
report.all = store.all();
console.log(JSON.stringify(report));""")

    def carry(self, values):
        text = run("console.log(JSON.stringify(encodeURIComponent(%s)))" % json.dumps(json.dumps(values)))
        return "#tok&carry=" + text

    def test_carried_settings_are_stored_and_leave_the_address(self):
        report = self.arrive(self.carry({"side": "left", "seekstep": "10"}))
        self.assertEqual(report["stored"], {"side": "left", "seekstep": "10"})
        self.assertEqual(report["url"], "#tok")

    def test_settings_already_here_are_kept(self):
        report = self.arrive(self.carry({"side": "left", "seekstep": "10"}), {"side": "right"})
        self.assertEqual(report["stored"], {"side": "right", "seekstep": "10"})

    def test_a_plain_address_is_left_alone(self):
        report = self.arrive("#tok", {"side": "left"})
        self.assertIsNone(report["url"])
        self.assertEqual(report["stored"], {"side": "left"})

    def test_a_damaged_carry_is_dropped(self):
        report = self.arrive("#tok&carry=%E0%A4%A")
        self.assertEqual(report["stored"], {})
        self.assertEqual(report["url"], "#tok")

    def test_everything_stored_can_be_read_back(self):
        self.assertEqual(self.arrive("#tok", {"side": "left"})["all"], {"side": "left"})


if __name__ == "__main__":
    unittest.main()
