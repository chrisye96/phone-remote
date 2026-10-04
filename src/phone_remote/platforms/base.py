"""每个操作系统要实现的统一接口。"""


def empty_media_state():
    """playing 为 True / False，读不到时为 None；pos 和 dur 是秒，vol 是 0-100。"""
    # kind is "music", "video" or "" (see mediakind.py); app is the name of what is playing it
    return {"playing": None, "title": "", "artist": "", "kind": "", "app": "",
            "pos": 0, "dur": 0, "vol": None, "muted": False}


class Platform:
    name = ""  # "win" 或 "mac"，手机页面用它决定按键写法

    def start(self):
        """启动后台任务（比如读取播放状态）。"""

    def stop(self):
        """退出前清理。"""

    def has_permission(self):
        """是否已经有模拟按键鼠标的权限。"""
        return True

    # 输入
    def press(self, mods, name):
        """按一次键。mods 是修饰键名列表，name 是 keys.KEYS 或 keys.SYSTEM_KEYS 里的名字。"""
        raise NotImplementedError

    def type_text(self, text):
        raise NotImplementedError

    def mouse_move(self, dx, dy):
        raise NotImplementedError

    def mouse_click(self, right=False):
        raise NotImplementedError

    def mouse_button(self, down):
        """Hold the left button down (True) or let it go (False); moving while it is down drags."""
        raise NotImplementedError

    def mouse_scroll(self, dy):
        """dy 为正表示向上滚，单位大致是像素。"""
        raise NotImplementedError

    # 窗口
    def list_windows(self):
        """返回 [{"id", "title", "app", "active"}]，按从前到后的顺序。"""
        raise NotImplementedError

    def focus_window(self, window_id):
        raise NotImplementedError

    # 媒体
    def media_state(self):
        return empty_media_state()

    def media_toggle(self):
        """让正在播放（或刚暂停）的那个程序播放 / 暂停，不管它在不在前台。

        做到了返回 True；没有可控制的播放时返回 False，调用方会改按空格。
        """
        return False

    def media_seek(self, seconds):
        """跳到指定秒数；做不到就什么都不做。"""
