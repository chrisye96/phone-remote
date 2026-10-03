"""托盘图标（Mac 上是菜单栏图标）：显示二维码、开机自启、退出。"""
import threading
import time
import webbrowser

from . import autostart, i18n, logo, update
from .i18n import t

try:
    import pystray
    import PIL  # noqa: F401  logo.render needs Pillow
except ImportError:  # 没装这两个库就退回到命令行窗口模式
    pystray = None


def available():
    return pystray is not None


def _icon_image():
    # The tray shows it at 16 to 32 px, so the small version of the logo, drawn with room to scale
    return logo.render(64, logo.SMALL)


def run(show_qr, on_quit, on_reset, on_language, check_updates=True):
    """显示托盘图标并一直运行，直到用户点“退出”。必须在主线程调用。"""
    def quit_app(icon, item):
        on_quit()
        icon.stop()

    def toggle_autostart(icon, item):
        autostart.set_enabled(not autostart.is_enabled())

    def language_item(code, name):
        def choose(icon, item):
            on_language(code)
            icon.title = t("Phone Remote")
            icon.update_menu()
        return pystray.MenuItem(name, choose, checked=lambda item: i18n.language == code, radio=True)

    newer = []  # holds the newer version's number once one is found

    def watch_for_updates(icon):
        while True:
            found = update.newer_version()
            if found and newer != [found]:
                newer[:] = [found]
                icon.update_menu()
            time.sleep(update.CHECK_EVERY)

    def ready(icon):
        icon.visible = True
        if check_updates:  # its own thread: pystray waits for this function when quitting
            threading.Thread(target=watch_for_updates, args=(icon,), daemon=True).start()

    # Labels are functions so the menu follows a language change without a restart
    menu = pystray.Menu(
        pystray.MenuItem(lambda item: t("Update available: v%s (opens the download page)") % "".join(newer),
                         lambda icon, item: webbrowser.open(update.RELEASES_PAGE), visible=lambda item: bool(newer)),
        pystray.MenuItem(lambda item: t("Show QR code"), lambda icon, item: show_qr(), default=True),
        pystray.MenuItem(lambda item: t("Start at login"), toggle_autostart, checked=lambda item: autostart.is_enabled()),
        pystray.MenuItem(lambda item: t("Re-pair (unpairs every phone)"), lambda icon, item: on_reset()),
        pystray.MenuItem(lambda item: t("Language"),
                         pystray.Menu(*[language_item(code, name) for code, name in i18n.LANGUAGES.items()])),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda item: t("Quit"), quit_app),
    )
    pystray.Icon("phone-remote", _icon_image(), t("Phone Remote"), menu).run(setup=ready)
