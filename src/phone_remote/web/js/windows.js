// 窗口列表：点一项就把那个窗口切到最前
import { send } from "./api.js";
import { t } from "./i18n.js";
import { onEnter } from "./nav.js";

const winList = document.getElementById("winlist");

function loadWindows() {
  if (!winList.isConnected) return;
  send({ a: "windows" }).then(list => {
    winList.textContent = "";
    if (!Array.isArray(list) || !list.length) {
      const p = document.createElement("p");
      p.textContent = list === false ? t("Can't read the window list") : t("No open windows");
      winList.appendChild(p);
      return;
    }
    list.forEach(w => {
      const btn = document.createElement("button");
      if (w.active) btn.className = "active";
      const avatar = document.createElement("span");
      avatar.className = "av";
      avatar.textContent = (w.app || w.title || "?").charAt(0).toUpperCase();
      const name = document.createElement("span");
      name.className = "name";
      name.textContent = w.title;
      if (w.app) { const app = document.createElement("small"); app.textContent = w.app; name.appendChild(app); }
      btn.append(avatar, name);
      if (w.active) { const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = t("Current"); btn.appendChild(tag); }
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
