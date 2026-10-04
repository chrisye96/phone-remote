"""测试用的假平台：不碰真实的键盘鼠标，只记录被调用了什么。"""
from phone_remote.platforms.base import Platform, empty_media_state


class FakePlatform(Platform):
    name = "win"

    def __init__(self):
        self.calls = []
        self.media = empty_media_state()
        self.can_toggle = True

    def press(self, mods, name):
        self.calls.append(("press", mods, name))

    def type_text(self, text):
        self.calls.append(("type_text", text))

    def mouse_move(self, dx, dy):
        self.calls.append(("mouse_move", dx, dy))

    def mouse_click(self, right=False):
        self.calls.append(("mouse_click", right))

    def mouse_button(self, down):
        self.calls.append(("mouse_button", down))

    def mouse_scroll(self, dy):
        self.calls.append(("mouse_scroll", dy))

    def list_windows(self):
        return [{"id": 1, "title": "Video", "app": "chrome", "active": True}]

    def focus_window(self, window_id):
        self.calls.append(("focus_window", window_id))

    def media_state(self):
        return self.media

    def media_toggle(self):
        self.calls.append(("media_toggle",))
        return self.can_toggle

    def media_seek(self, seconds):
        self.calls.append(("media_seek", seconds))
