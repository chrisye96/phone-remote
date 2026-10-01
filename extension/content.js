// 手机遥控器会按 F13–F21 这些键盘上没有的键，这里把它们翻译成对视频的操作。
const RATES = { F13: 0.75, F14: 1, F15: 1.25, F16: 1.5, F17: 2, F18: 3 };
const SEEKS = { F19: -30, F20: 30, F21: 90 };

window.addEventListener("keydown", e => {
  const command = e.key in RATES ? { rate: RATES[e.key] } : e.key in SEEKS ? { seek: SEEKS[e.key] } : null;
  if (!command) return;
  e.preventDefault();
  e.stopImmediatePropagation();
  chrome.runtime.sendMessage(command);
}, true);

function pickVideo() {
  const videos = [...document.querySelectorAll("video")].filter(v => v.readyState > 0);
  const area = v => v.clientWidth * v.clientHeight;
  return videos.find(v => !v.paused) || videos.sort((a, b) => area(b) - area(a))[0];
}

let tip, tipTimer;
function showTip(text) {
  if (!tip) {
    tip = document.createElement("div");
    tip.style.cssText = "position:fixed;top:24px;left:24px;z-index:2147483647;padding:8px 16px;border-radius:10px;" +
      "background:rgba(0,0,0,.75);color:#fff;font:600 22px system-ui,sans-serif;pointer-events:none;transition:opacity .3s";
  }
  tip.textContent = text;
  tip.style.opacity = "1";
  (document.fullscreenElement || document.documentElement).appendChild(tip);
  clearTimeout(tipTimer);
  tipTimer = setTimeout(() => { tip.style.opacity = "0"; }, 1200);
}

chrome.runtime.onMessage.addListener(command => {
  const video = pickVideo();
  if (!video) return;
  if (command.rate) {
    video.playbackRate = command.rate;
    showTip(command.rate + "×");
  } else if (command.seek) {
    const end = Number.isFinite(video.duration) ? video.duration : Infinity;
    video.currentTime = Math.max(0, Math.min(end, video.currentTime + command.seek));
    showTip((command.seek > 0 ? "+" : "") + command.seek + " 秒");
  }
});
