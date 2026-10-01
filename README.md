# 手机遥控器

在电脑上运行一个小程序，手机浏览器打开网页，就能遥控电脑上的视频播放：音量、播放暂停、快进快退、触控板、滚动、文字输入，以及 B 站、YouTube、浏览器和 AI 客户端的常用快捷键。

只用 Python 标准库，Windows 和 macOS 通用。手机和电脑需要在同一个 Wi-Fi 下。

## 运行

Windows：双击 `start-windows.bat`。

macOS：

```bash
PYTHONPATH=src python3 -m phone_remote
```

第一次在 Mac 上运行，需要在 系统设置 > 隐私与安全性 > 辅助功能 里给"终端"授权。

启动后电脑会弹出二维码页面，用手机相机扫码即可。

## 遥控器的四个页面

- **播放**：圆盘控制音量、快进快退、播放暂停；下面是全屏等常用键，以及通用 / B 站 / YouTube 的专用键。
- **触控板**：移动鼠标、单击、双击、右键、滚动，外加浏览器的后退、标签切换、缩放。
- **输入**：在手机上打字或听写，发到电脑当前的输入框；还有回车、退格等按键。
- **窗口**：列出电脑上打开的窗口，点一下切换过去；可以最大化、最小化、移到另一块屏幕。Mac 上列出的是应用。

## 功能开关

每个功能都可以单独关掉。第一次运行后会生成配置文件（启动时会打印它的位置，Windows 上在 `%APPDATA%\PhoneRemote\config.json`），把 `features` 里对应的一项改成 `false`，重启程序即可。关掉后电脑端会拒绝对应的指令，手机页面上也不再显示那一块。

| 开关 | 功能 |
|---|---|
| `touchpad` | 触控板：移动鼠标、点击、滚动 |
| `text_input` | 文字输入 |
| `windows` | 窗口列表和切换 |
| `play_state` | 显示正在播放还是暂停，以及标题 |
| `progress` | 进度条、拖动跳转、±30 秒 |
| `volume_display` | 显示音量数值 |
| `sleep_timer` | 定时暂停 |
| `open_sites` | 快速打开网站 |
| `site_keys` | B 站、YouTube 的专用按键 |
| `browser_keys` | 浏览器按键 |

音量、播放暂停、快进快退和基本按键是核心功能，不能关。

## 代码结构

```
src/phone_remote/
  __main__.py      入口
  config.py        端口、配对码、功能开关
  server.py        HTTP 服务器：页面文件、配对校验
  actions.py       指令校验和分发
  keys.py          按键名表、组合键解析
  timer.py         定时暂停
  pairing.py       二维码页面
  platforms/       每个系统一套实现，其他代码只用 base.py 里的接口
    base.py
    windows/       input.py  windows.py  media.py
    macos/         input.py  windows.py  media.py
  web/             手机页面：index.html、css/、js/（按功能分模块）
tests/             自动测试，不碰真实的键盘鼠标
docs/              重构计划
```

运行测试：双击 `run-tests.bat`，或

```bash
PYTHONPATH="src;tests" python -m unittest discover -s tests
```

## 分支

- `main`：可以直接用的稳定版本。
- `dev`：日常开发。新功能从 `dev` 拉 `feature/*` 分支，完成后合回 `dev`，验证过再合到 `main`。
