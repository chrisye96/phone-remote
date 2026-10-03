"""Interface language for what the computer shows: tray menu, QR page, console output.

The code is written in English; other languages are looked up here by the English text.
The phone page has its own table in web/js/i18n.js.
"""
LANGUAGES = {"en": "English", "zh": "中文"}
DEFAULT = "en"

_TABLES = {
    "zh": {
        "Phone Remote": "手机遥控器",
        # tray menu
        "Show QR code": "显示二维码",
        "Start at login": "开机自动启动",
        "Re-pair (unpairs every phone)": "重新配对（已配对的手机全部失效）",
        "Language": "语言",
        "Quit": "退出",
        "Update available: v%s (opens the download page)": "有新版本 v%s（点击打开下载页）",
        "A newer version is available: v%s": "有新版本可用：v%s",
        # console
        "Port %d is already in use. Phone Remote is probably running already.": "端口 %d 已被占用，程序可能已经在运行。",
        "Phone Remote is running. Open this address on your phone, or scan the QR code that just opened:":
            "手机遥控器已启动。手机打开这个网址（或扫电脑上弹出的二维码）：",
        "No permission to control this computer yet. Open System Settings > Privacy & Security > Accessibility,":
            "还没有控制权限：打开 系统设置 > 隐私与安全性 > 辅助功能，",
        "turn on the app that runs this program, then start it again.": "把运行本程序的应用打开，然后重新启动本程序。",
        "Feature switches are in this file: %s": "功能开关在这个文件里：%s",
        "Keep this window open while you use the remote. Closing it quits.": "用的时候保持这个窗口开着，关掉窗口就是退出。",
        "Only Windows and macOS are supported.": "只支持 Windows 和 macOS。",
        # QR page
        "Scan with your phone's camera": "用手机相机扫码",
        "Your phone and this computer need to be on the same Wi-Fi.": "手机和这台电脑需要连在同一个 Wi-Fi 上。",
        "Can't scan? Open this address in your phone's browser:": "扫不了？在手机浏览器里打开这个地址：",
        "Copy": "复制",
        "Add the page to your home screen to open it like an app next time.":
            "打开后“添加到主屏幕”，下次像 App 一样点图标就能用。",
        "This code is the key to this computer, so keep it to yourself. If it gets out, choose Re-pair in the tray menu.":
            "这个二维码是这台电脑的钥匙，不要发给别人。万一泄露，在托盘菜单里点“重新配对”。",
        "This code is the key to this computer, so keep it to yourself. If it gets out, restart with --reset-pairing.":
            "这个二维码是这台电脑的钥匙，不要发给别人。万一泄露，加上 --reset-pairing 重新启动。",
        "You can close this page. Phone Remote keeps running in the system tray; right-click its icon to see this page again or to quit.":
            "这个页面可以关掉。程序留在任务栏右下角的托盘里，右键它的图标可以再次打开这个页面，或者退出。",
        "You can close this page. Phone Remote keeps running in the menu bar; click its icon to see this page again or to quit.":
            "这个页面可以关掉。程序留在屏幕顶部的菜单栏里，点它的图标可以再次打开这个页面，或者退出。",
        "You can close this page, but keep the Phone Remote terminal window open.":
            "这个页面可以关掉，但不要关闭遥控器的命令行窗口。",
    },
}

language = DEFAULT


def set_language(code):
    global language
    language = code if code in LANGUAGES else DEFAULT


def t(text):
    return _TABLES.get(language, {}).get(text, text)
