"""配对：算出手机要打开的网址，并生成电脑上显示的二维码页面。"""
import html
import json
import socket
import sys

from . import i18n
from .i18n import t

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


_PAIR_PAGE = """<!doctype html><html lang="__LANG__"><meta charset="utf-8"><title>__TITLE__</title>
<style>body{font-family:system-ui,sans-serif;background:#14161a;color:#eee;text-align:center;padding:40px 24px;line-height:1.6}
h1{margin:0 0 6px}p{color:#aab;margin:6px 0}
#qr{display:inline-block;background:#fff;padding:12px;border-radius:12px;margin:22px}#qr svg{display:block}
#copy{font:inherit;color:#eee;background:#262a31;border:1px solid transparent;border-radius:10px;padding:10px 14px;margin:8px 0 22px;
cursor:pointer;display:inline-flex;align-items:center;gap:12px;max-width:100%}
#copy:hover{border-color:#4b5261}#copy code{font-size:19px;overflow-wrap:anywhere}
#copy svg{width:22px;height:22px;flex:none;color:#aab}#copy.done svg{color:#3ddc97}
.notes{max-width:620px;margin:0 auto;font-size:14px}</style>
<h1>__HEADING__</h1><p>__WIFI__</p><div id="qr">__QR__</div>
<p>__MANUAL__</p>
<button id="copy" type="button" title="__COPY__" aria-label="__COPY__"><code>__URL__</code><svg><use href="/icons.svg#copy"/></svg></button>
<div class="notes"><p>__SECRET__</p><p>__HOME__</p><p>__HINT__</p></div>
<script type="module" src="/js/pair.js"></script>__SCRIPT__</html>"""
_CDN_SCRIPT = """<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>new QRCode(document.getElementById("qr"),{text:__URL_JSON__,width:260,height:260})</script>"""
_SECRET = "This code is the key to this computer, so keep it to yourself. If it gets out, "
_TRAY_HINT = ("You can close this page. Phone Remote keeps running in the system tray; "
              "right-click its icon to see this page again or to quit.")
_MAC_HINT = ("You can close this page. Phone Remote keeps running in the menu bar; "
             "click its icon to see this page again or to quit.")
_CONSOLE_HINT = "You can close this page, but keep the Phone Remote terminal window open."


def pair_page(url, tray_mode=False):
    if segno:
        qr, script = segno.make(url, error="m").svg_inline(scale=7, border=1), ""
    else:
        # 不让网址里的内容提前结束脚本标签
        safe = json.dumps(url).replace("<", r"\u003c")
        qr, script = "", _CDN_SCRIPT.replace("__URL_JSON__", safe)
    if tray_mode:
        secret, hint = _SECRET + "choose Re-pair in the tray menu.", _MAC_HINT if sys.platform == "darwin" else _TRAY_HINT
    else:
        secret, hint = _SECRET + "restart with --reset-pairing.", _CONSOLE_HINT
    texts = {"__TITLE__": "Phone Remote", "__HEADING__": "Scan with your phone's camera",
             "__WIFI__": "Your phone and this computer need to be on the same Wi-Fi.",
             "__MANUAL__": "Can't scan? Open this address in your phone's browser:", "__COPY__": "Copy",
             "__HOME__": "Add the page to your home screen to open it like an app next time.",
             "__SECRET__": secret, "__HINT__": hint}
    page = _PAIR_PAGE.replace("__LANG__", i18n.language)
    for mark, text in texts.items():
        page = page.replace(mark, html.escape(t(text)))
    # The address goes in last so nothing in it can be mistaken for one of the marks above
    return page.replace("__QR__", qr).replace("__SCRIPT__", script).replace("__URL__", html.escape(url))
