"""入口：python -m phone_remote

默认在托盘里运行，没有窗口；加 --console 则在命令行窗口里运行并打印信息。
"""
import argparse
import logging
import threading
import webbrowser

from . import config as config_module
from . import tray
from .actions import Dispatcher
from .pairing import phone_url
from .platforms import get_platform
from .server import make_server

log = logging.getLogger("phone_remote")


def main():
    parser = argparse.ArgumentParser(prog="phone_remote", description="手机遥控器")
    parser.add_argument("--console", action="store_true", help="在命令行窗口里运行，不用托盘图标")
    parser.add_argument("--background", action="store_true", help="启动时不弹出二维码页面（开机自启用）")
    parser.add_argument("--no-browser", action="store_true", help="同 --background")
    args = parser.parse_args()
    quiet = args.background or args.no_browser

    config = config_module.load()
    logging.basicConfig(filename=config.data_dir / "phone-remote.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    pair_url = "http://127.0.0.1:%d/pair" % config.port

    def show_qr():
        webbrowser.open(pair_url)

    platform = get_platform()
    url = phone_url(config.port, config.token)
    try:
        server = make_server(config.port, config.token, Dispatcher(platform, config.features), url)
    except OSError:
        # 端口被占用，多半是已经有一个在运行了，那就只把二维码页面打开
        log.warning("port %d is in use, assuming another instance is running", config.port)
        print("端口 %d 已被占用，程序可能已经在运行。" % config.port)
        if not quiet:
            show_qr()
        return

    use_tray = tray.available() and not args.console
    server.tray_mode = use_tray
    log.info("started on port %d, tray=%s", config.port, use_tray)
    print("手机遥控器已启动。手机打开这个网址（或扫电脑上弹出的二维码）：")
    print("  " + url)
    if not platform.has_permission():
        log.warning("no accessibility permission")
        print("\n还没有控制权限：打开 系统设置 > 隐私与安全性 > 辅助功能，")
        print("把运行本程序的应用打开，然后重新启动本程序。")
    print("\n功能开关在这个文件里：%s" % (config.data_dir / "config.json"))

    platform.start()
    if not quiet:
        show_qr()
    try:
        if use_tray:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            tray.run(show_qr, on_quit=server.shutdown)
        else:
            print("用的时候保持这个窗口开着，关掉窗口就是退出。")
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
