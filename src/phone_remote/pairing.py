"""配对：算出手机要打开的网址，并生成电脑上显示的二维码页面。"""
import socket


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
#qr{display:inline-block;background:#fff;padding:16px;border-radius:12px;margin:24px}
code{font-size:20px;background:#262a31;padding:8px 14px;border-radius:8px}p{color:#aab}</style>
<h1>用 iPhone 相机扫码</h1><div id="qr"></div>
<p>手机和这台电脑要连同一个 Wi-Fi。扫不了就在手机浏览器里输入：</p><code>__URL__</code>
<p>打开后可以在 Safari 里“添加到主屏幕”，下次直接点图标。<br>这个页面可以关掉，但不要关闭遥控器的黑色窗口。</p>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>new QRCode(document.getElementById("qr"),{text:"__URL__",width:260,height:260})</script></html>"""


def pair_page(url):
    return _PAIR_PAGE.replace("__URL__", url)
