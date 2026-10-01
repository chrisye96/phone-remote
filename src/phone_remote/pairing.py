"""配对：算出手机要打开的网址，并生成电脑上显示的二维码页面。"""
import html
import json
import socket

try:
    import segno
except ImportError:  # 没装就退回到从网上加载二维码脚本
    segno = None


def lan_ip():
    # 不会真的发送数据，只是让系统选出通往局域网的网卡地址
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


def phone_url(port, token):
    return "http://%s:%d/#%s" % (lan_ip(), port, token)


_PAIR_PAGE = """<!doctype html><html lang="zh"><meta charset="utf-8"><title>手机遥控器</title>
<style>body{font-family:system-ui,sans-serif;background:#14161a;color:#eee;text-align:center;padding:48px}
#qr{display:inline-block;background:#fff;padding:12px;border-radius:12px;margin:24px}#qr svg{display:block}
code{font-size:20px;background:#262a31;padding:8px 14px;border-radius:8px}p{color:#aab}</style>
<h1>用手机相机扫码</h1><div id="qr">__QR__</div>
<p>手机和这台电脑要连同一个 Wi-Fi。扫不了就在手机浏览器里输入：</p><code>__URL__</code>
<p>打开后可以“添加到主屏幕”，下次直接点图标。<br>__HINT__</p>__SCRIPT__</html>"""
_CDN_SCRIPT = """<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>new QRCode(document.getElementById("qr"),{text:__URL_JSON__,width:260,height:260})</script>"""
_TRAY_HINT = "这个页面可以关掉。程序在任务栏右下角的托盘里运行，右键它的图标可以退出。"
_CONSOLE_HINT = "这个页面可以关掉，但不要关闭遥控器的命令行窗口。"


def pair_page(url, tray_mode=False):
    if segno:
        qr, script = segno.make(url, error="m").svg_inline(scale=7, border=1), ""
    else:
        # 不让网址里的内容提前结束脚本标签
        safe = json.dumps(url).replace("<", r"\u003c")
        qr, script = "", _CDN_SCRIPT.replace("__URL_JSON__", safe)
    return (_PAIR_PAGE.replace("__QR__", qr).replace("__SCRIPT__", script)
            .replace("__HINT__", _TRAY_HINT if tray_mode else _CONSOLE_HINT)
            .replace("__URL__", html.escape(url)))
