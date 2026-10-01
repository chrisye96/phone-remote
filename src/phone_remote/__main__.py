"""入口：python -m phone_remote"""
import argparse
import webbrowser

from . import config as config_module
from .actions import Dispatcher
from .pairing import phone_url
from .platforms import get_platform
from .server import make_server


def main():
    parser = argparse.ArgumentParser(prog="phone_remote", description="手机遥控器")
    parser.add_argument("--no-browser", action="store_true", help="启动时不弹出二维码页面")
    args = parser.parse_args()

    config = config_module.load()
    platform = get_platform()
    url = phone_url(config.port, config.token)
    server = make_server(config.port, config.token, Dispatcher(platform, config.features), url)

    print("手机遥控器已启动。手机打开这个网址（或扫电脑上弹出的二维码）：")
    print("  " + url)
    if not platform.has_permission():
        print("\n还没有控制权限：打开 系统设置 > 隐私与安全性 > 辅助功能，")
        print("把运行本程序的“终端”打开，然后重新启动本程序。")
    print("\n功能开关在这个文件里：%s" % (config.data_dir / "config.json"))
    print("用的时候保持这个窗口开着，关掉窗口就是退出。")

    platform.start()
    if not args.no_browser:
        webbrowser.open("http://127.0.0.1:%d/pair" % config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        platform.stop()


if __name__ == "__main__":
    main()
