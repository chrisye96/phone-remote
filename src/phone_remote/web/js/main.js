// 入口：先把页面各部分接好，再向电脑问清楚它是什么系统、开了哪些功能
import { env, send, token } from "./api.js";
import { initButtons } from "./buttons.js";
import { initMedia } from "./media.js";
import { initNav, setSite } from "./nav.js";
import { initShortcuts, renderShortcuts } from "./shortcuts.js";
import { setHost } from "./status.js";
import { initText } from "./text.js";
import { initTimer } from "./timer.js";
import { initTouchpads } from "./touchpad.js";
import { initWindows } from "./windows.js";

initButtons();
initTouchpads();
initText();
initWindows();
initMedia();
initTimer();
initShortcuts();
initNav();

// 去掉这台电脑用不上的部分：别的系统专用的按键、被关掉的功能
function applyEnvironment(info) {
  env.platform = info.platform;
  setHost(info.host);
  document.querySelectorAll("[data-only]").forEach(el => { if (el.dataset.only !== info.platform) el.remove(); });
  document.querySelectorAll("[data-feature]").forEach(el => { if (info.features[el.dataset.feature] === false) el.remove(); });
  // 里面的东西都被去掉了的行和面板，一起去掉
  document.querySelectorAll(".row, .site").forEach(el => { if (!el.children.length && el.id !== "shortcuts") el.remove(); });
  document.querySelectorAll(".group, .card").forEach(el => { if (!el.querySelector("button, #now, #prog, #shortcuts")) el.remove(); });
  renderShortcuts(info.shortcuts || [], info.max_shortcuts);
  const selected = document.querySelector(".tabs button.sel");
  setSite(selected ? selected.dataset.site : "any");
}

let connected = false;
function connect() {
  if (connected || !token) { if (!token) send({ a: "ping" }); return; }
  send({ a: "hello" }).then(info => {
    if (info && typeof info === "object") { connected = true; applyEnvironment(info); send({ a: "ping" }); }
    else setTimeout(connect, 3000);
  });
}
connect();
document.addEventListener("visibilitychange", () => { if (!document.hidden) { if (connected) send({ a: "ping" }); else connect(); } });
