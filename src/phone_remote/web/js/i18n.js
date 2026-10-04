// Interface language. The page and the scripts are written in English; other languages are looked up
// here by the English text. A label missing from a table simply stays English.
import { store } from "./store.js";

const TABLES = {
  zh: {
    // header and connection
    "Remote": "遥控器",
    "Connecting…": "正在连接…",
    "Connected": "已连接",
    "Switch computer": "切换电脑",
    "Language": "语言",
    "Not paired yet: scan the QR code on the computer": "还没配对：请扫电脑上的二维码打开",
    "Pairing no longer valid: scan the QR code on the computer again": "配对失效：请重新扫电脑上的二维码",
    "Too many failed attempts: the computer ignores this device for 5 minutes": "错误次数太多：电脑暂时不接受这台设备的指令，5 分钟后再试",
    "Clocks don't match: reopen this page": "和电脑的时间对不上：请重新打开这个页面",
    "Can't reach the computer: check that the program is running and both are on the same Wi-Fi": "连不上电脑：检查程序是否开着、是否同一个 Wi-Fi",
    "Muted": "已静音",
    "Volume {n}": "音量 {n}",

    // touchpad
    "Slide to move, tap to click": "滑动移动鼠标　轻点单击",
    "Two fingers: tap to right-click, slide to scroll": "双指轻点右键　双指滑动滚动",
    "Hold, then slide to drag": "按住不动，再滑动是拖动",

    // play
    "Fullscreen": "全屏",
    "Exit": "退出",
    "OK": "确定",
    "General": "通用",
    "Bilibili": "B站",
    "Music": "音乐",
    "Video": "视频",
    "Back 30s": "退 30 秒",
    "Fwd 30s": "进 30 秒",
    "Back 10s": "退 10 秒",
    "Fwd 10s": "进 10 秒",
    "Skip intro": "跳片头",
    "Sleep timer": "定时暂停",
    "{n} min left": "剩 {n} 分钟",
    "Pausing in {n} min": "{n} 分钟后暂停",
    "Timer cancelled": "已取消定时",
    "Up": "上",
    "Down": "下",
    "Subtitles": "字幕",
    "Space": "空格",
    "Prev episode": "上一集",
    "Next episode": "下一集",
    "Danmaku": "弹幕",
    "Like": "点赞",
    "Player volume": "播放器音量",
    "Mute": "静音",
    "Favorite": "收藏",
    "Prev video": "上一个",
    "Next video": "下一个",
    "Theater": "影院模式",
    "Slower": "减速",
    "Faster": "加速",
    "Prev track": "上一首",
    "Next track": "下一首",
    "Volume down": "音量减",
    "Volume up": "音量加",
    "Rewind": "快退",
    "Play or pause": "播放或暂停",
    "Fast forward": "快进",

    // browse
    "Page": "页面",
    "Back": "后退",
    "Forward": "前进",
    "Reload": "刷新",
    "Zoom out": "缩小",
    "Zoom in": "放大",
    "Tabs": "标签页",
    "Prev tab": "上一个",
    "Next tab": "下一个",
    "New tab": "新建",
    "Close tab": "关闭",
    "Sites": "常用",
    "Hold one to edit it": "长按可以修改",
    "+ Add": "+ 添加",
    "Opened {name} on the computer": "已在电脑上打开 {name}",
    "Add shortcut": "添加快捷方式",
    "Edit shortcut": "修改快捷方式",
    "Address": "网址",
    "Name": "名称",
    "Leave empty to use the page's own title": "留空则自动读取网页名称",
    "Cancel": "取消",
    "Save": "保存",
    "Delete this shortcut": "删除这个快捷方式",
    "Enter an address first": "先填网址",
    "Reading the page…": "正在读取网页…",
    "Can't save: the address should look like bilibili.com or https://…": "保存不了：网址要像 bilibili.com 或 https://… 这样",

    // type
    "Type here, or tap the mic on your keyboard to dictate": "在这里打字，或点键盘上的麦克风说话",
    "Type only": "只输入",
    "Type and press Enter": "输入并回车",
    "Type something above first": "先在上面输入文字",
    "Typed and pressed Enter": "已输入并回车",
    "Typed": "已输入",
    "Enter": "回车",
    "New line": "换行",
    "Backspace": "退格",
    "Select all": "全选",
    "Undo": "撤销",
    "Stop": "停止",
    "Dictate on PC": "电脑听写",
    "New AI chat": "AI 新对话",
    "Address bar": "地址栏",

    // windows
    "Tap a window to bring it to the front": "点一下切换到那个窗口",
    "Current window": "当前窗口",
    "To other screen": "移到另一块屏幕",
    "Minimize": "最小化",
    "Maximize": "最大化",
    "Last window": "上一个窗口",
    "All windows": "全部窗口",
    "Page fullscreen": "网页全屏",
    "Can't read the window list": "读取不到窗口列表",
    "No open windows": "没有打开的窗口",
    "Current": "当前",

    // navigation
    "Play": "播放",
    "Browse": "浏览",
    "Type": "输入",
    "Windows": "窗口",

    // computers
    "Not paired": "未配对",
    "Add computer…": "添加电脑…",
    "Rename {name}…": "给 {name} 改名…",
    "Remove {name}": "移除 {name}",
    "Remove {name}? You will have to add it again to use it.": "移除 {name}？以后要用需要重新添加。",
    "Add computer": "添加电脑",
    "Rename this computer": "给这台电脑改名",
    "Add and switch": "添加并切换",
    "Address shown on that computer's QR page": "那台电脑二维码页面上的网址",
    "192.168.1.5:8765/#code": "192.168.1.5:8765/#配对码",
    "Scan that computer's QR code with your camera, hold the link it finds and choose Copy Link, then paste it here. The address is stored only on this device.":
      "用相机扫那台电脑的二维码，长按识别出的链接选“拷贝链接”，再粘贴到这里。网址只保存在这台设备上。",
    "Leave empty to use the computer's own name": "留空则用电脑自己的名字",
    "Incomplete address: it should look like 192.168.1.5:8765/#code, including the part after #": "网址不完整：要像 192.168.1.5:8765/#配对码 这样，# 后面的也要带上",
    "This computer is already added": "这台电脑已经添加过了",
  },
};

export const lang = TABLES[store.get("lang")] ? store.get("lang") : "en";
const table = TABLES[lang] || {};

// Translates one piece of text; {name} style placeholders are filled in from values
export function t(text, values) {
  let result = table[text] || text;
  for (const key in values || {}) result = result.replace("{" + key + "}", values[key]);
  return result;
}

// Translates what is written in index.html: visible text, placeholders and labels for screen readers
function translatePage() {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.nodeValue.trim();
    if (table[text]) node.nodeValue = node.nodeValue.replace(text, table[text]);
  }
  ["placeholder", "aria-label"].forEach(attribute => document.querySelectorAll("[" + attribute + "]").forEach(el => {
    el.setAttribute(attribute, t(el.getAttribute(attribute)));
  }));
  document.title = t(document.title);
  document.documentElement.lang = lang;
}

export function initLanguage() {
  if (lang !== "en") translatePage();
  document.documentElement.classList.remove("translating");
  const button = document.getElementById("lang");
  button.querySelectorAll("[data-lang]").forEach(el => el.classList.toggle("sel", el.dataset.lang === lang));
  // Two languages, so one tap switches to the other. The page reloads because labels are set in many places.
  button.addEventListener("click", () => { store.set("lang", lang === "en" ? "zh" : "en"); location.reload(); });
}
