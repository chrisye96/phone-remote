"""托盘图标（Mac 上是菜单栏图标）：显示二维码、开机自启、退出。"""
from . import autostart

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:  # 没装这两个库就退回到命令行窗口模式
    pystray = None


def available():
    return pystray is not None


def _icon_image(size=64):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, size - 2, size - 2), radius=size // 4, fill=(108, 140, 255, 255))
    draw.polygon([(size * 0.38, size * 0.27), (size * 0.38, size * 0.73), (size * 0.75, size * 0.5)],
                 fill=(255, 255, 255, 255))
    return image


def run(show_qr, on_quit):
    """显示托盘图标并一直运行，直到用户点“退出”。必须在主线程调用。"""
    def quit_app(icon, item):
        on_quit()
        icon.stop()

    def toggle_autostart(icon, item):
        autostart.set_enabled(not autostart.is_enabled())

    menu = pystray.Menu(
        pystray.MenuItem("显示二维码", lambda icon, item: show_qr(), default=True),
        pystray.MenuItem("开机自动启动", toggle_autostart, checked=lambda item: autostart.is_enabled()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", quit_app),
    )
    pystray.Icon("phone-remote", _icon_image(), "手机遥控器", menu).run()
