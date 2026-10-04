// Settings sheet behind the gear in the header: interface language, and which side the touchpad
// sits on when the screen is wide. Each choice applies as soon as it is tapped.
import { active } from "./api.js";
import { label } from "./devices.js";
import { lang, t } from "./i18n.js";
import { store } from "./store.js";

const sheet = document.getElementById("setsheet");
const langChoices = document.getElementById("setlang"), sideChoices = document.getElementById("setside");
const versionLine = document.getElementById("setversion");

// Right unless the user chose left: most people steer the pointer with their right thumb
const side = () => (store.get("side") === "left" ? "left" : "right");

function mark(choices, value) {
  choices.querySelectorAll("button").forEach(b => b.classList.toggle("sel", b.dataset.value === value));
}
function applySide() {
  document.body.classList.toggle("lefty", side() === "left");
  mark(sideChoices, side());
}
// Calls back with the value of whichever choice was tapped
function onChoice(choices, fn) {
  choices.addEventListener("click", e => { const b = e.target.closest("button"); if (b) fn(b.dataset.value); });
}

export function initSettings() {
  applySide();
  mark(langChoices, lang);
  document.getElementById("gear").addEventListener("click", () => {
    const known = active && active.version;
    versionLine.hidden = !known;
    if (known) versionLine.textContent = t("Phone Remote {v} on {name}", { v: active.version, name: label(active) });
    sheet.hidden = false;
  });
  // The page reloads for a new language because labels are set in many places
  onChoice(langChoices, value => { if (value !== lang) { store.set("lang", value); location.reload(); } });
  onChoice(sideChoices, value => { store.set("side", value); applySide(); });
  document.getElementById("setform").addEventListener("submit", e => { e.preventDefault(); sheet.hidden = true; });
  sheet.addEventListener("pointerdown", e => { if (e.target === sheet) sheet.hidden = true; });
}
