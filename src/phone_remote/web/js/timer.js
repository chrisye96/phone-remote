// 定时暂停：每按一次换一档
import { send } from "./api.js";
import { onState, pollState } from "./media.js";
import { toast } from "./status.js";

const STEPS = [15, 30, 60, 90, 0];
const button = document.getElementById("timer");
const label = button.querySelector("small");
let step = -1;

export function initTimer() {
  onState(state => { label.textContent = state.timer ? "剩 " + Math.ceil(state.timer / 60) + " 分钟" : "关"; });
  button.addEventListener("pointerdown", () => {
    button.classList.add("on");
    step = (step + 1) % STEPS.length;
    const min = STEPS[step];
    send({ a: "timer", min }).then(ok => { if (ok) { toast(min ? min + " 分钟后暂停" : "已取消定时"); pollState(); } });
  });
  ["pointerup", "pointercancel", "pointerleave"].forEach(t => button.addEventListener(t, () => button.classList.remove("on")));
}
