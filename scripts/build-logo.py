"""Writes every logo file from src/phone_remote/logo.py. Run it again after changing the logo:
    .venv\\Scripts\\python scripts\\build-logo.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phone_remote import logo  # noqa: E402

WEB = ROOT / "src" / "phone_remote" / "web"


def main():
    (WEB / "favicon.svg").write_text(logo.svg(logo.SMALL), encoding="utf-8", newline="\n")
    (ROOT / "docs" / "logo.svg").write_text(logo.svg(logo.FULL), encoding="utf-8", newline="\n")
    logo.render(32, logo.SMALL).save(WEB / "favicon-32.png")
    logo.render(180, bleed=True).save(WEB / "apple-touch-icon.png")  # iOS rounds the corners itself
    # Android home screen icons, listed in web/manifest.webmanifest. The maskable ones fill the square,
    # because Android cuts them to whatever shape the launcher uses.
    for size in (192, 512):
        logo.render(size).save(WEB / ("icon-%d.png" % size))
        logo.render(size, bleed=True).save(WEB / ("icon-maskable-%d.png" % size))
    # Windows picks the closest size from the .ico, so each size gets the design drawn for it
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [logo.render(s, logo.for_size(s)) for s in sizes]
    images[-1].save(ROOT / "scripts" / "phone-remote.ico", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    for name in ("favicon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
                 "icon-maskable-192.png", "icon-maskable-512.png"):
        print(WEB / name)
    print(ROOT / "docs" / "logo.svg")
    print(ROOT / "scripts" / "phone-remote.ico")


if __name__ == "__main__":
    main()
