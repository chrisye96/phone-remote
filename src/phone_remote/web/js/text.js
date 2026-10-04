// Text input: type or dictate on the phone, and it is typed into whatever has focus on the computer.
// While typing, the text box takes over the screen so long text is easy to see; line breaks are kept.
import { send } from "./api.js";
import { t } from "./i18n.js";
import { toast } from "./status.js";

const textInput = document.getElementById("text");
const box = textInput.closest(".compose");

function expand(on) {
  box.classList.toggle("expanded", on);
  if (!on) textInput.blur();
}

// The on-screen keyboard covers the bottom of the page without resizing it, so track what is still visible
function fitAboveKeyboard() {
  const view = window.visualViewport;
  if (!view) return;
  document.documentElement.style.setProperty("--vvh", view.height + "px");
  document.documentElement.style.setProperty("--vvt", view.offsetTop + "px");
}

function sendText(enter) {
  const text = textInput.value.trim();
  if (!text && !enter) { toast(t("Type something above first")); return; }
  send({ a: "text", t: text, enter }).then(ok => {
    if (!ok) return;
    textInput.value = "";
    expand(false);
    toast(enter ? t("Typed and pressed Enter") : t("Typed"));
  });
}

export function initText() {
  document.getElementById("sendText").addEventListener("click", () => sendText(false));
  document.getElementById("sendEnter").addEventListener("click", () => sendText(true));
  // Not collapsed on blur: tapping a button blurs the box first, and the button must not move from under the finger
  ["focus", "click"].forEach(type => textInput.addEventListener(type, () => { fitAboveKeyboard(); expand(true); }));
  document.getElementById("closeText").addEventListener("click", () => expand(false));
  if (window.visualViewport) ["resize", "scroll"].forEach(type => window.visualViewport.addEventListener(type, fitAboveKeyboard));
}
