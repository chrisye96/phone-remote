// 窗口列表：点一项就把那个窗口切到最前
import { send } from "./api.js";
import { onEnter } from "./nav.js";

const winList = document.getElementById("winlist");

function loadWindows() {
  if (!winList.isConnected) return;
  send({ a: "windows" }).then(list => {
    winList.textContent = "";
    if (!Array.isArray(list) || !list.length) {
      const p = document.createElement("p");
      p.textContent = list === false ? "读取不到窗口列表" : "没有打开的窗口";
      winList.appendChild(p);
      return;
    }
    list.forEach(w => {
      const btn = document.createElement("button");
      if (w.active) btn.className = "active";
      if (w.app) { const app = document.createElement("small"); app.textContent = w.app; btn.appendChild(app); }
      btn.appendChild(document.createTextNode(w.title));
      btn.addEventListener("click", () => send({ a: "focus", id: w.id }).then(() => setTimeout(loadWindows, 350)));
      winList.appendChild(btn);
    });
  });
}

export function initWindows() {
  onEnter("wins", loadWindows);
  // 按了最大化、切换之类的键以后，列表顺序会变
  document.querySelectorAll("#winkeys button").forEach(b => b.addEventListener("pointerup", () => setTimeout(loadWindows, 500)));
}
