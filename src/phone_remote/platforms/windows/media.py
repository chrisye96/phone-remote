"""Windows：读播放状态、进度和音量，并跳转进度。

用的是系统的“媒体控制”接口，浏览器和大多数播放器都支持。
这些接口目前通过一个常驻的 PowerShell 子进程调用（media_helper.ps1）：
它每半秒输出一行 JSON 状态，并从标准输入读指令（seek 秒数）。
注意：浏览器上报“播放 / 暂停”可能晚十秒左右，跳转则一秒内就能读到。
"""
import base64
import json
import os
import subprocess
import threading
from pathlib import Path

from ..base import empty_media_state

HELPER = Path(__file__).with_name("media_helper.ps1")
NO_WINDOW = 0x08000000
PLAYING = {"Playing": True, "Paused": False, "Stopped": False}


class MediaWatcher:
    def __init__(self):
        self._state = empty_media_state()
        self._proc = None

    def start(self):
        exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                           "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        script = HELPER.read_text(encoding="utf-8")
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        try:
            self._proc = subprocess.Popen(
                [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
        except OSError:
            return
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self._proc.stdout:
            try:
                state = json.loads(line)
            except ValueError:
                continue
            self._state = {
                "playing": PLAYING.get(state["s"]), "title": state["t"] or "",
                "pos": state["p"], "dur": state["d"],
                "vol": state["v"] if state["v"] >= 0 else None, "muted": bool(state["m"]),
            }

    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.stdin.close()  # 子进程读到输入结束就自己退出

    def state(self):
        return self._state

    def seek(self, seconds):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.stdin.write("seek %.1f\n" % seconds)
                self._proc.stdin.flush()
            except OSError:
                pass
