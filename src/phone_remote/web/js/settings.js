// Settings sheet behind the gear in the header: interface language, which side the touchpad sits on
// when the screen is wide, and how far the General tab jumps. Each choice applies as soon as it is tapped.
import { active } from "./api.js";
import { label } from "./devices.js";
import { lang, t } from "./i18n.js";
import { choose } from "./press.js";
import { store } from "./store.js";

const sheet = document.getElementById("setsheet");
const langChoices = document.getElementById("setlang"), sideChoices = document.getElementById("setside");
const seekChoices = document.getElementById("setseek");
const versionLine = document.getElementById("setversion");

// Right unless the user chose left: most people steer the pointer with their right thumb
const side = () => (store.get("side") === "left" ? "left" : "right");

function mark(choices, value) {
  choose(choices.querySelectorAll("button"), "value", value);
}
function applySide() {
  document.body.classList.toggle("lefty", side() === "left");
  mark(sideChoices, side());
}
// Seconds the General tab's Back and Fwd keys jump: the stored choice while it is still on offer, otherwise 15
function seekStep() {
  const stored = store.get("seekstep");
  return [...seekChoices.children].some(b => b.dataset.value === stored) ? stored : "15";
}
// The number is drawn into the icon, so the icon changes along with the distance and the label
function applySeekStep() {
  const step = seekStep();
  document.querySelectorAll("button[data-step]").forEach(b => {
    const back = b.dataset.step === "backward";
    b.dataset.rel = back ? -step : step;
    b.querySelector("use").setAttribute("href", "icons.svg#rewind-" + b.dataset.step + "-" + step);
    b.querySelector("span").textContent = t(back ? "Back {n}s" : "Fwd {n}s", { n: step });
  });
  mark(seekChoices, step);
}
// Calls back with the value of whichever choice was tapped
function onChoice(choices, fn) {
  choices.addEventListener("click", e => { const b = e.target.closest("button"); if (b) fn(b.dataset.value); });
}

export function initSettings() {
  applySide();
  applySeekStep();
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
  onChoice(seekChoices, value => { store.set("seekstep", value); applySeekStep(); });
  document.getElementById("setform").addEventListener("submit", e => { e.preventDefault(); sheet.hidden = true; });
  sheet.addEventListener("pointerdown", e => { if (e.target === sheet) sheet.hidden = true; });
}
