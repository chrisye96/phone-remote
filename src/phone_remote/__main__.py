"""入口：python -m phone_remote

默认在托盘里运行，没有窗口；加 --console 则在命令行窗口里运行并打印信息。
"""
import argparse
import logging
import threading
import webbrowser

from . import config as config_module
from . import i18n, tray, update
from .actions import Dispatcher
from .i18n import t
from .pairing import phone_url
from .platforms import get_platform
from .server import make_server

log = logging.getLogger("phone_remote")


def main():
    parser = argparse.ArgumentParser(prog="phone_remote", description="Phone Remote: control this computer from your phone's browser")
    parser.add_argument("--console", action="store_true", help="run in this terminal window instead of the system tray")
    parser.add_argument("--background", action="store_true", help="do not open the QR page on start (used when starting at login)")
    parser.add_argument("--no-browser", action="store_true", help="same as --background")
    parser.add_argument("--reset-pairing", action="store_true", help="make a new pairing code; every paired phone has to scan again")
    args = parser.parse_args()
    quiet = args.background or args.no_browser

    config = config_module.load()
    i18n.set_language(config.language)
    if args.reset_pairing:
        config_module.reset_token(config)
    logging.basicConfig(filename=config.data_dir / "phone-remote.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    pair_url = "http://127.0.0.1:%d/pair" % config.port

    def show_qr():
        webbrowser.open(pair_url)

    def current_url():
        # Worked out each time: the address changes when the computer joins another network (a phone hotspot)
        return phone_url(config.port, config.token)

    def change_language(code):
        config.language = code
        config_module.save(config)
        i18n.set_language(code)

    def announce_update():
        found = update.newer_version()
        if found:
            print("\n" + t("A newer version is available: v%s") % found + "  " + update.RELEASES_PAGE)

    def reset_pairing():
        config_module.reset_token(config)
        server.token = config.token
        log.info("pairing reset")
        show_qr()

    platform = get_platform()
    url = current_url()
    try:
        dispatcher = Dispatcher(platform, config.features, shortcuts=config.shortcuts,
                                on_change=lambda: config_module.save(config))
        server = make_server(config.port, config.token, dispatcher, current_url)
    except OSError:
        # 端口被占用，多半是已经有一个在运行了，那就只把二维码页面打开
        log.warning("port %d is in use, assuming another instance is running", config.port)
        print(t("Port %d is already in use. Phone Remote is probably running already.") % config.port)
        if not quiet:
            show_qr()
        return

    use_tray = tray.available() and not args.console
    server.tray_mode = use_tray
    server.has_permission = platform.has_permission
    log.info("started on port %d, tray=%s", config.port, use_tray)
    print(t("Phone Remote is running. Open this address on your phone, or scan the QR code that just opened:"))
    print("  " + url)
    if not platform.has_permission():
        log.warning("no accessibility permission")
        print("\n" + t("No permission to control this computer yet. Open System Settings > Privacy & Security > Accessibility,"))
        print(t("turn on the app that runs this program, then start it again."))
    print("\n" + t("Feature switches are in this file: %s") % (config.data_dir / "config.json"))

    platform.start()
    if not quiet:
        show_qr()
    try:
        if use_tray:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            tray.run(show_qr, on_quit=server.shutdown, on_reset=reset_pairing, on_language=change_language,
                     check_updates=config.check_updates)
        else:
            print(t("Keep this window open while you use the remote. Closing it quits."))
            if config.check_updates:
                threading.Thread(target=announce_update, daemon=True).start()
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception:
        log.exception("stopped by an error")
        raise
    finally:
        platform.stop()
        log.info("stopped")


if __name__ == "__main__":
    main()
