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

// Same condition as the tablet rules in css/app.css
const roomy = window.matchMedia("(min-width:700px) and (min-height:600px)");

export function setSite(site) {
  if (!document.getElementById(site)) site = "any";
  // A tablet always shows the general keys, so there the tabs only choose among the sites
  if (roomy.matches && site === "any") site = document.getElementById(store.get("lastsite")) ? store.get("lastsite") : "bili";
  if (!document.getElementById(site)) site = "any";   // the site keys are switched off on this computer
  if (site !== "any") store.set("lastsite", site);
  pick(".tabs button[data-site]", "site", site, "site");
  document.querySelectorAll(".site").forEach(d => d.classList.toggle("sel", d.id === site));
  // 整块面板的边框跟着选中的网站变色
  const color = document.getElementById(site).style.getPropertyValue("--site");
  document.getElementById("sitegroup").style.setProperty("--site", color || "transparent");
}

export function initNav() {
  document.querySelectorAll("nav button").forEach(b => b.addEventListener("pointerdown", () => go(b.dataset.go)));
  document.querySelectorAll(".tabs button[data-site]").forEach(b => b.addEventListener("pointerdown", () => setSite(b.dataset.site)));
  // 网址里可以带 ?screen=browse&site=bili 直接打开某一页
  const query = new URLSearchParams(location.search);
  const screen = query.get("screen") || store.get("screen") || "";
  // An empty name (first visit, nothing stored yet) would make an invalid selector and stop the whole page
  go(screen && document.querySelector("section.screen#" + CSS.escape(screen)) ? screen : "play");
  setSite(query.get("site") || store.get("site") || "any");
  roomy.addEventListener("change", () => setSite(store.get("site") || "any"));
}
