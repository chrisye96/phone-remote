"""配置：端口、配对码、功能开关，以及它们存在哪。"""
import json
import os
import secrets
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PORT = 8765

# 每个功能一个开关，在 config.json 的 "features" 里改成 false 就关掉。
# 关掉后电脑端拒绝对应的指令，手机页面也不显示对应的部分。
FEATURES = {
    "touchpad": "触控板：移动鼠标、点击、滚动",
    "text_input": "文字输入：手机上打字或听写，输入到电脑",
    "windows": "窗口列表和切换",
    "play_state": "显示正在播放还是暂停，以及标题",
    "progress": "进度条、拖动跳转、±30 秒",
    "volume_display": "显示音量数值",
    "sleep_timer": "定时暂停",
    "open_sites": "网页快捷方式",
    "site_keys": "B 站、YouTube 的专用按键",
    "browser_keys": "浏览器按键：后退、标签、缩放",
}


MAX_SHORTCUTS = 4
DEFAULT_SHORTCUTS = [
    {"name": "B站", "url": "https://www.bilibili.com", "color": "#fb7299"},
    {"name": "YouTube", "url": "https://www.youtube.com", "color": "#ff4e45"},
]


@dataclass
class Config:
    port: int = DEFAULT_PORT
    saved_port: int = DEFAULT_PORT  # 配置文件里写的端口；port 可能被环境变量临时改掉
    token: str = ""
    features: dict = field(default_factory=lambda: dict.fromkeys(FEATURES, True))
    shortcuts: list = field(default_factory=lambda: [dict(s) for s in DEFAULT_SHORTCUTS])
    data_dir: Path = Path(".")


def data_dir():
    override = os.environ.get("REMOTE_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "PhoneRemote"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PhoneRemote"
    return Path.home() / ".phone-remote"


def _load_token(folder):
    token_file = folder / "token.txt"
    legacy = Path("token.txt")  # 重构前配对码放在程序旁边，沿用它就不用重新扫码
    for candidate in (token_file, legacy):
        if candidate.exists():
            token = candidate.read_text(encoding="utf-8").strip()
            if token:
                token_file.write_text(token, encoding="utf-8")
                return token
    token = secrets.token_hex(8)
    token_file.write_text(token, encoding="utf-8")
    return token


def save(config):
    (config.data_dir / "config.json").write_text(
        json.dumps({"port": config.saved_port, "features": config.features, "shortcuts": config.shortcuts},
                   indent=2, ensure_ascii=False),
        encoding="utf-8")


def load():
    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    config = Config(data_dir=folder)
    config_file = folder / "config.json"
    saved = {}
    if config_file.exists():
        try:
            saved = json.loads(config_file.read_text(encoding="utf-8"))
        except ValueError:
            saved = {}
    config.port = config.saved_port = int(saved.get("port", DEFAULT_PORT))
    for name, enabled in saved.get("features", {}).items():
        if name in FEATURES:
            config.features[name] = bool(enabled)
    if isinstance(saved.get("shortcuts"), list):
        config.shortcuts = [
            {"name": str(s.get("name", ""))[:12], "url": str(s.get("url", "")), "color": str(s.get("color", ""))}
            for s in saved["shortcuts"]
            if isinstance(s, dict) and str(s.get("url", "")).startswith(("https://", "http://"))
        ][:MAX_SHORTCUTS]
    save(config)  # 每次写回，这样新增的功能开关会出现在文件里，方便修改
    if os.environ.get("REMOTE_PORT"):
        config.port = int(os.environ["REMOTE_PORT"])
    config.token = _load_token(folder)
    return config
