import json
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from phone_remote import logo

WEB = Path(__file__).parent.parent / "src" / "phone_remote" / "web"


class LogoTest(unittest.TestCase):
    def test_svg_is_well_formed_and_has_the_play_button_and_arcs(self):
        for design, arcs in ((logo.FULL, 2), (logo.SMALL, 1)):
            root = ElementTree.fromstring(logo.svg(design))
            paths = root.findall("{http://www.w3.org/2000/svg}path")
            self.assertEqual(len(paths), 1 + arcs)

    def test_render_draws_the_tile_and_leaves_the_corners_clear(self):
        image = logo.render(64, logo.SMALL)
        self.assertEqual(image.size, (64, 64))
        self.assertEqual(image.getpixel((0, 0))[3], 0)  # rounded corner stays transparent
        self.assertEqual(image.getpixel((8, 32))[:3], (0x10, 0x23, 0x3a))  # navy tile
        self.assertEqual(logo.render(32, bleed=True).getpixel((0, 0))[3], 255)

    def test_generated_files_match_the_module(self):
        # scripts/build-logo.py writes them; this fails if the logo changed and the files were not rebuilt
        self.assertEqual((WEB / "favicon.svg").read_text(encoding="utf-8"), logo.svg(logo.SMALL))

    def test_manifest_lists_icons_that_exist_in_the_shape_android_expects(self):
        from PIL import Image

        manifest = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
        # iOS would open start_url instead of the address that was added, and so lose the #token
        self.assertNotIn("start_url", manifest)
        self.assertEqual({(i["sizes"], i["purpose"]) for i in manifest["icons"]},
                         {(s, p) for s in ("192x192", "512x512") for p in ("any", "maskable")})
        for icon in manifest["icons"]:
            with self.subTest(icon=icon["src"]):
                image = Image.open(WEB / icon["src"])
                self.assertEqual("%dx%d" % image.size, icon["sizes"])
                # Android cuts a maskable icon to its own shape, so it must be filled to the corners
                self.assertEqual(image.getpixel((0, 0))[3], 255 if icon["purpose"] == "maskable" else 0)

    def test_logo_stays_inside_the_part_of_a_maskable_icon_that_is_never_cut_off(self):
        # Android may cut the icon down to a circle 80% as wide; nothing but the tile may fall outside it
        size = 200
        image = logo.render(size, bleed=True)
        tile = image.getpixel((0, 0))
        for x in range(size):
            for y in range(size):
                if (x - size / 2 + .5) ** 2 + (y - size / 2 + .5) ** 2 > (size * .4) ** 2:
                    self.assertEqual(image.getpixel((x, y)), tile, (x, y))


if __name__ == "__main__":
    unittest.main()
