"""添加网页快捷方式时，去读一下那个网页的名称和代表色。读不到就用网址里的域名和一个固定算出来的颜色。"""
import colorsys
import hashlib
import io
import re
import urllib.request
from urllib.parse import urljoin, urlparse

try:
    from PIL import Image
except ImportError:  # 没装就不从图标里取颜色
    Image = None

TIMEOUT = 4
MAX_PAGE = 400_000
MAX_ICON = 300_000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _download(url, limit):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(limit), response.headers.get_content_charset() or "utf-8"


def _tags(html, tag):
    """页面里某种标签的属性，每个标签一个字典。"""
    found = []
    for raw in re.findall(r"<%s\b([^>]*)>" % tag, html, re.I):
        attrs = re.findall(r"([\w:-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'>]+))", raw)
        found.append({name.lower(): (a or b or c).strip() for name, a, b, c in attrs})
    return found


def fallback_name(url):
    host = urlparse(url).hostname or url
    return host[4:] if host.startswith("www.") else host


def fallback_color(url):
    """同一个网站每次算出同一个颜色。"""
    hue = int(hashlib.md5(fallback_name(url).encode()).hexdigest()[:4], 16) / 0xFFFF
    r, g, b = colorsys.hls_to_rgb(hue, 0.62, 0.65)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def parse_name(html, url):
    metas = _tags(html, "meta")
    for key in ("og:site_name", "application-name", "apple-mobile-web-app-title"):
        for meta in metas:
            if key in (meta.get("property"), meta.get("name")) and meta.get("content"):
                return meta["content"][:12]
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if title:
        # 标题常常是“页面名 - 网站名 - 口号”，取第一段
        first = re.split(r"\s*[-|_–—·:：,，(（]\s*", " ".join(title.group(1).split()))[0]
        if first:
            return first[:12]
    return fallback_name(url)[:12]


def parse_theme_color(html):
    for meta in _tags(html, "meta"):
        if meta.get("name", "").lower() == "theme-color" and HEX_COLOR.match(meta.get("content", "")):
            color = meta["content"].lower()
            if color not in ("#fff", "#ffffff", "#000", "#000000"):
                return color
    return None


def parse_icon_url(html, url):
    for link in _tags(html, "link"):
        if "icon" in link.get("rel", "").lower() and link.get("href"):
            return urljoin(url, link["href"])
    return urljoin(url, "/favicon.ico")


def dominant_color(image_bytes):
    """图标里最有代表性的颜色：不透明、不是黑白灰的那些像素的平均值。"""
    if Image is None:
        return None
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA").resize((24, 24))
    except Exception:
        return None
    total, count = [0, 0, 0], 0
    for r, g, b, a in image.getdata():
        if a < 128:
            continue
        _, lightness, saturation = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if saturation > 0.3 and 0.15 < lightness < 0.9:
            total[0] += r; total[1] += g; total[2] += b
            count += 1
    if count < 12:
        return None
    return "#%02x%02x%02x" % tuple(round(c / count) for c in total)


def readable(color):
    """界面是深色的，太暗的颜色看不见，调亮到看得清为止。"""
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    r, g, b = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    if lightness >= 0.55:
        return "#" + value.lower()
    r, g, b = colorsys.hls_to_rgb(hue, 0.62, saturation)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def fetch(url):
    """返回 {"name", "color"}。任何一步失败都有兜底，不会抛异常。"""
    info = {"name": fallback_name(url)[:12], "color": fallback_color(url)}
    try:
        data, charset = _download(url, MAX_PAGE)
        try:
            html = data.decode(charset, "replace")
        except LookupError:
            html = data.decode("utf-8", "replace")
    except Exception:
        return info
    info["name"] = parse_name(html, url)
    color = parse_theme_color(html)
    if not color:
        try:
            color = dominant_color(_download(parse_icon_url(html, url), MAX_ICON)[0])
        except Exception:
            color = None
    if color:
        info["color"] = readable(color)
    return info
