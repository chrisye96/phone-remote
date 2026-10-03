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


if __name__ == "__main__":
    unittest.main()
