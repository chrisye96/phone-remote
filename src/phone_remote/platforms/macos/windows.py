"""macOS：目前按应用切换，列出有界面的应用。"""
from .script import osascript


def list_windows():
    names = osascript('tell application "System Events" to get name of every process '
                      'whose background only is false')
    front = osascript('tell application "System Events" to get name of first process '
                      'whose frontmost is true')
    return [{"id": name, "title": name, "app": "", "active": name == front}
            for name in (n.strip() for n in names.split(",")) if name]


def focus_window(name):
    if name not in [w["id"] for w in list_windows()]:
        raise ValueError("no such app")
    osascript("on run argv",
              'tell application "System Events" to set frontmost of process (item 1 of argv) to true',
              "end run", args=[name])
