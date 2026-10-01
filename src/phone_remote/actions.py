"""把手机发来的指令校验后交给平台实现去执行。"""
import re
import socket
import webbrowser

from . import siteinfo
from .config import MAX_SHORTCUTS
from .keys import parse_combo
from .timer import SleepTimer

# 指令 -> 它属于哪个功能开关；不在表里的是核心功能，不能关
ACTION_FEATURE = {
    "move": "touchpad", "click": "touchpad", "scroll": "touchpad",
    "text": "text_input",
    "windows": "windows", "focus": "windows",
    "seek": "progress",
    "timer": "sleep_timer",
    "open": "open_sites", "shortcut_save": "open_sites", "shortcut_delete": "open_sites",
}


BARE_HOST = re.compile(r"^[\w-]+(\.[\w-]+)+([/:?#]|$)")


class FeatureDisabled(Exception):
    pass


def clamp(value, limit):
    return max(-limit, min(limit, int(value)))


class Dispatcher:
    def __init__(self, platform, features, opener=webbrowser.open,
                 shortcuts=None, on_change=None, site_info=siteinfo.fetch):
        self.platform = platform
        self.features = features
        self.shortcuts = shortcuts if shortcuts is not None else []
        self._on_change = on_change or (lambda: None)  # 快捷方式改动后调用，用来存盘
        self._site_info = site_info
        self.timer = SleepTimer(platform)
        self._open = opener

    def enabled(self, feature):
        return self.features.get(feature, True)

    def handle(self, msg):
        """执行一条指令。没有返回值的指令返回 None。"""
        action = msg.get("a")
        feature = ACTION_FEATURE.get(action)
        if feature and not self.enabled(feature):
            raise FeatureDisabled(feature)
        handler = getattr(self, "_do_" + str(action), None)
        if handler is None:
            raise ValueError("unknown action")
        return handler(msg)

    def _do_ping(self, msg):
        pass

    def _do_hello(self, msg):
        return {"platform": self.platform.name, "host": socket.gethostname(),
                "features": self.features,
                "shortcuts": self.shortcuts, "max_shortcuts": MAX_SHORTCUTS}

    def _do_state(self, msg):
        state = dict(self.platform.media_state())
        if not self.enabled("play_state"):
            state.update(playing=None, title="")
        if not self.enabled("progress"):
            state.update(pos=0, dur=0)
        if not self.enabled("volume_display"):
            state.update(vol=None, muted=False)
        state["timer"] = self.timer.remaining()
        return state

    def _do_playpause(self, msg):
        # 优先让系统去通知正在播放的程序，这样音乐软件在后台、视频没被点中时也有效
        if not self.platform.media_toggle():
            self.platform.press([], "space")

    def _do_seek(self, msg):
        self.platform.media_seek(float(msg.get("to", 0)))

    def _do_timer(self, msg):
        self.timer.set(float(msg.get("min", 0)))

    def _shortcut_index(self, msg):
        index = msg.get("i")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(self.shortcuts):
            raise ValueError("no such shortcut")
        return index

    def _do_open(self, msg):
        # 只能打开已保存的快捷方式，手机发不了任意网址过来
        self._open(self.shortcuts[self._shortcut_index(msg)]["url"])

    def _do_shortcut_save(self, msg):
        """新增（不带 i）或修改（带 i）一个快捷方式。名称留空就用网页自己的名称。"""
        url = str(msg.get("url", "")).strip()
        if "://" not in url and BARE_HOST.match(url):  # 允许只写 bilibili.com 这样的
            url = "https://" + url
        if not url.startswith(("https://", "http://")) or len(url) > 500 or " " in url:
            raise ValueError("bad url")
        index = self._shortcut_index(msg) if msg.get("i") is not None else None
        if index is None and len(self.shortcuts) >= MAX_SHORTCUTS:
            raise ValueError("too many shortcuts")
        info = self._site_info(url)
        name = " ".join(str(msg.get("name", "")).split())[:12] or info["name"]
        shortcut = {"name": name, "url": url, "color": info["color"]}
        if index is None:
            self.shortcuts.append(shortcut)
        else:
            self.shortcuts[index] = shortcut
        self._on_change()
        return self.shortcuts

    def _do_shortcut_delete(self, msg):
        del self.shortcuts[self._shortcut_index(msg)]
        self._on_change()
        return self.shortcuts

    def _do_windows(self, msg):
        return self.platform.list_windows()

    def _do_focus(self, msg):
        self.platform.focus_window(msg.get("id"))

    def _do_key(self, msg):
        self.platform.press(*parse_combo(msg.get("k")))

    def _do_text(self, msg):
        text = " ".join(str(msg.get("t", "")).split())[:2000]
        if text:
            self.platform.type_text(text)
        if msg.get("enter"):
            self.platform.press([], "enter")

    def _do_move(self, msg):
        self.platform.mouse_move(clamp(msg.get("dx", 0), 2000), clamp(msg.get("dy", 0), 2000))

    def _do_click(self, msg):
        self.platform.mouse_click(right=bool(msg.get("right")))

    def _do_scroll(self, msg):
        self.platform.mouse_scroll(clamp(msg.get("dy", 0), 1500))
