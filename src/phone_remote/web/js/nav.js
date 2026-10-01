// 底部导航和网站分页，记住上次的选择
import { store } from "./api.js";

const enterHandlers = {};

// 进入某个页面时要做的事
export function onEnter(screen, fn) { enterHandlers[screen] = fn; }

function pick(selector, attr, value, storeKey) {
  document.querySelectorAll(selector).forEach(b => b.classList.toggle("sel", b.dataset[attr] === value));
  store.set(storeKey, value);
}

export function go(screen) {
  document.body.dataset.screen = screen;
  pick("nav button", "go", screen, "screen");
  if (document.activeElement) document.activeElement.blur();
  if (enterHandlers[screen]) enterHandlers[screen]();
}

export function setSite(site) {
  if (!document.getElementById(site)) site = "any";
  pick(".chips button[data-site]", "site", site, "site");
  document.querySelectorAll(".site").forEach(d => d.classList.toggle("sel", d.id === site));
}

export function initNav() {
  document.querySelectorAll("nav button").forEach(b => b.addEventListener("pointerdown", () => go(b.dataset.go)));
  document.querySelectorAll(".chips button[data-site]").forEach(b => b.addEventListener("pointerdown", () => setSite(b.dataset.site)));
  go(document.getElementById(store.get("screen") || "") ? store.get("screen") : "play");
  setSite(store.get("site") || "any");
}
