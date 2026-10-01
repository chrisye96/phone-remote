"""把用到的图标合成一个文件 src/phone_remote/web/icons.svg。

图标来自 Tabler Icons（MIT 协议）。要增减图标时改下面的名单，然后：
    npm install @tabler/icons          （在任意临时目录里）
    python scripts/build-icons.py <那个目录>/node_modules/@tabler/icons/icons
"""
import re
import sys
from pathlib import Path

OUTLINE = """
device-tv world keyboard app-window volume volume-2 volume-off maximize arrows-minimize check
chevron-up chevron-down chevron-left chevron-right hand-finger message-2 thumb-up star minus plus
rewind-backward-30 rewind-forward-30 rewind-backward-10 rewind-forward-10 hourglass badge-cc space
arrow-up arrow-down arrow-left arrow-right refresh zoom-in zoom-out x send corner-down-left
arrow-bar-down backspace select-all arrow-back-up arrow-bar-to-right microphone message-plus link
switch-horizontal layout-grid screen-share arrows-maximize rectangle trash player-skip-forward
player-skip-back player-stop gauge
""".split()
FILLED = "player-play player-pause player-track-next player-track-prev".split()

OUTLINE_ATTRS = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
FILLED_ATTRS = 'fill="currentColor"'


def symbol(path, name, attrs):
    body = re.search(r"<svg[^>]*>(.*)</svg>", path.read_text(encoding="utf-8"), re.S).group(1)
    body = body.replace('<path stroke="none" d="M0 0h24v24H0z" fill="none"/>', "")
    body = " ".join(body.split())
    return '<symbol id="%s" viewBox="0 0 24 24"><g %s>%s</g></symbol>' % (name, attrs, body)


def main():
    source = Path(sys.argv[1])
    symbols = [symbol(source / "outline" / (n + ".svg"), n, OUTLINE_ATTRS) for n in OUTLINE]
    symbols += [symbol(source / "filled" / (n + ".svg"), n, FILLED_ATTRS) for n in FILLED]
    target = Path(__file__).resolve().parent.parent / "src" / "phone_remote" / "web" / "icons.svg"
    target.write_text(
        "<!-- Tabler Icons, MIT License, Copyright (c) 2020-2024 Paweł Kuna. 由 scripts/build-icons.py 生成 -->\n"
        '<svg xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(symbols) + "\n</svg>\n",
        encoding="utf-8", newline="\n")
    print("%d icons -> %s (%d bytes)" % (len(symbols), target, target.stat().st_size))


if __name__ == "__main__":
    main()
