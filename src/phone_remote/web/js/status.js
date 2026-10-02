// 顶部的连接状态和弹出提示
import { t } from "./i18n.js";

const dot = document.getElementById("dot");
const statusText = document.getElementById("status");
const toastBox = document.getElementById("toast");
let toastTimer;

export function toast(text, bad) {
  toastBox.textContent = text;
  toastBox.className = "show" + (bad ? " bad" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastBox.className = ""; }, bad ? 4000 : 1200);
}

export function setStatus(ok, text) {
  if (!ok && dot.className !== "bad") toast(text, true);
  dot.className = ok ? "ok" : "bad";
  statusText.textContent = ok ? t("Connected") : text;
}
