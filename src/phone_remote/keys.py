"""按键名表和组合键解析，和操作系统无关。"""

SYSTEM_KEYS = ("volup", "voldown", "mute", "media")
MODIFIERS = ("ctrl", "shift", "alt", "win", "mod")  # mod = Windows 的 Ctrl / Mac 的 Command

# 按键名: (Windows 虚拟键码, macOS 键码)
KEYS = {
    "space": (0x20, 49), "enter": (0x0D, 36), "esc": (0x1B, 53), "tab": (0x09, 48),
    "backspace": (0x08, 51), "delete": (0x2E, 117),
    "left": (0x25, 123), "right": (0x27, 124), "up": (0x26, 126), "down": (0x28, 125),
    "pageup": (0x21, 116), "pagedown": (0x22, 121), "home": (0x24, 115), "end": (0x23, 119),
    "[": (0xDB, 33), "]": (0xDD, 30), ",": (0xBC, 43), ".": (0xBE, 47), "/": (0xBF, 44),
    ";": (0xBA, 41), "'": (0xDE, 39), "-": (0xBD, 27), "=": (0xBB, 24), "`": (0xC0, 50),
}
_MAC_LETTERS = dict(a=0, s=1, d=2, f=3, h=4, g=5, z=6, x=7, c=8, v=9, b=11, q=12, w=13,
                    e=14, r=15, y=16, t=17, o=31, u=32, i=34, p=35, l=37, j=38, k=40, n=45, m=46)
_MAC_DIGITS = [29, 18, 19, 20, 21, 23, 22, 26, 28, 25]
_MAC_FKEYS = [122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111]
for _letter, _code in _MAC_LETTERS.items():
    KEYS[_letter] = (ord(_letter.upper()), _code)
for _digit, _code in enumerate(_MAC_DIGITS):
    KEYS[str(_digit)] = (0x30 + _digit, _code)
for _n, _code in enumerate(_MAC_FKEYS):
    KEYS["f%d" % (_n + 1)] = (0x70 + _n, _code)


def parse_combo(combo):
    """'ctrl+shift+n' -> (['ctrl', 'shift'], 'n')"""
    *mods, name = str(combo).lower().split("+")
    if any(m not in MODIFIERS for m in mods):
        raise ValueError("unknown modifier")
    if name not in KEYS and not (name in SYSTEM_KEYS and not mods):
        raise ValueError("unknown key")
    return mods, name
