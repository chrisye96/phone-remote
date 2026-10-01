import io
import unittest

from phone_remote import siteinfo

PAGE = """<html><head>
<title>哔哩哔哩 (゜-゜)つロ 干杯~-bilibili</title>
<meta name="theme-color" content="#FB7299">
<link rel="shortcut icon" href="/static/favicon.ico">
</head></html>"""


class ParseTest(unittest.TestCase):
    def test_name_prefers_site_name_meta(self):
        html = '<meta property="og:site_name" content="YouTube"><title>Home - YouTube</title>'
        self.assertEqual(siteinfo.parse_name(html, "https://www.youtube.com"), "YouTube")

    def test_name_falls_back_to_first_part_of_title(self):
        self.assertEqual(siteinfo.parse_name(PAGE, "https://www.bilibili.com"), "哔哩哔哩")
        self.assertEqual(siteinfo.parse_name("<title>  爱壹帆 | 海外华人影视  </title>", "https://x.tv"), "爱壹帆")

    def test_name_falls_back_to_host(self):
        self.assertEqual(siteinfo.parse_name("<html></html>", "https://www.example.com/a"), "example.com")

    def test_name_is_capped(self):
        self.assertEqual(len(siteinfo.parse_name("<title>%s</title>" % ("长" * 50), "https://x.tv")), 12)

    def test_theme_color(self):
        self.assertEqual(siteinfo.parse_theme_color(PAGE), "#fb7299")
        self.assertIsNone(siteinfo.parse_theme_color('<meta name="theme-color" content="#ffffff">'))
        self.assertIsNone(siteinfo.parse_theme_color('<meta name="theme-color" content="red">'))
        self.assertIsNone(siteinfo.parse_theme_color("<html></html>"))

    def test_icon_url(self):
        self.assertEqual(siteinfo.parse_icon_url(PAGE, "https://www.bilibili.com/video/1"),
                         "https://www.bilibili.com/static/favicon.ico")
        self.assertEqual(siteinfo.parse_icon_url("<html></html>", "https://a.example/b/c"),
                         "https://a.example/favicon.ico")

    def test_fallback_color_is_stable_and_valid(self):
        color = siteinfo.fallback_color("https://www.example.com")
        self.assertEqual(color, siteinfo.fallback_color("https://example.com/other"))
        self.assertRegex(color, r"^#[0-9a-f]{6}$")

    @unittest.skipIf(siteinfo.Image is None, "需要 Pillow")
    def test_dominant_color_ignores_white_and_transparent(self):
        image = siteinfo.Image.new("RGBA", (16, 16), (255, 255, 255, 255))
        for x in range(8):
            for y in range(16):
                image.putpixel((x, y), (250, 30, 40, 255))
        data = io.BytesIO()
        image.save(data, "PNG")
        self.assertRegex(siteinfo.dominant_color(data.getvalue()), r"^#f[9a][12]\w[23]\w$")  # 接近红色那一半
        self.assertIsNone(siteinfo.dominant_color(b"not an image"))

    def test_dark_colors_are_lightened(self):
        self.assertEqual(siteinfo.readable("#fb7299"), "#fb7299")
        self.assertEqual(siteinfo.readable("#FFF"), "#ffffff")
        for dark in ("#090b21", "#1e2327", "#000"):
            r, g, b = (int(siteinfo.readable(dark)[i:i + 2], 16) for i in (1, 3, 5))
            self.assertGreater(max(r, g, b), 140, dark)

    def test_fetch_never_raises(self):
        info = siteinfo.fetch("http://127.0.0.1:9/nothing-here")
        self.assertEqual(info["name"], "127.0.0.1")
        self.assertRegex(info["color"], r"^#[0-9a-f]{6}$")


if __name__ == "__main__":
    unittest.main()
