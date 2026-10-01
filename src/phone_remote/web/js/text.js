// 文字输入：手机上打字或听写，发到电脑当前的输入框里
import { send } from "./api.js";
import { toast } from "./status.js";

const textInput = document.getElementById("text");

function sendText(enter) {
  const t = textInput.value.trim();
  if (!t && !enter) { toast("先在上面输入文字"); return; }
  send({ a: "text", t, enter }).then(ok => { if (ok) { textInput.value = ""; toast(enter ? "已输入并回车" : "已输入"); } });
}

export function initText() {
  document.getElementById("sendText").addEventListener("click", () => sendText(false));
  document.getElementById("sendEnter").addEventListener("click", () => sendText(true));
  textInput.addEventListener("keydown", e => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); sendText(true); } });
}
