// 定时暂停：每按一次换一档
import { send } from "./api.js";
import { t } from "./i18n.js";
import { onState, pollState } from "./media.js";
import { toast } from "./status.js";

const STEPS = [15, 30, 60, 90, 0];
const button = document.getElementById("timer");
const label = button.querySelector("span");
let step = -1;

export function initTimer() {
  onState(state => {
    label.textContent = state.timer ? t("{n} min left", { n: Math.ceil(state.timer / 60) }) : t("Sleep timer");
    button.classList.toggle("c-play", !!state.timer);
  });
  button.addEventListener("pointerdown", () => {
    button.classList.add("on");
    step = (step + 1) % STEPS.length;
    const min = STEPS[step];
    send({ a: "timer", min }).then(ok => { if (ok) { toast(min ? t("Pausing in {n} min", { n: min }) : t("Timer cancelled")); pollState(); } });
  });
  ["pointerup", "pointercancel", "pointerleave"].forEach(type => button.addEventListener(type, () => button.classList.remove("on")));
}
