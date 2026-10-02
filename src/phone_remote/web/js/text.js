// 文字输入：手机上打字或听写，发到电脑当前的输入框里
import { send } from "./api.js";
import { t } from "./i18n.js";
import { toast } from "./status.js";

const textInput = document.getElementById("text");

function sendText(enter) {
  const text = textInput.value.trim();
  if (!text && !enter) { toast(t("Type something above first")); return; }
  send({ a: "text", t: text, enter }).then(ok => { if (ok) { textInput.value = ""; toast(enter ? t("Typed and pressed Enter") : t("Typed")); } });
}

export function initText() {
  document.getElementById("sendText").addEventListener("click", () => sendText(false));
  document.getElementById("sendEnter").addEventListener("click", () => sendText(true));
  textInput.addEventListener("keydown", e => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); sendText(true); } });
}
