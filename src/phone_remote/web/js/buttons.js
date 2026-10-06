// 通用按钮：按下立即触发，带 data-repeat 的长按连发
import { env, send } from "./api.js";
import { onPress } from "./press.js";

// data-cmd name -> function that builds the message, for commands that carry more than their name
export const commands = {};

function command(btn) {
  if (btn.dataset.cmd) return commands[btn.dataset.cmd] ? commands[btn.dataset.cmd]() : { a: btn.dataset.cmd };
  if (btn.dataset.scroll) return { a: "scroll", dy: Number(btn.dataset.scroll) };
  if (btn.dataset.open) return { a: "open", url: btn.dataset.open };
  return { a: "key", k: (env.platform === "mac" && btn.dataset.mac) || btn.dataset.k };
}

export function initButtons() {
  document.querySelectorAll("button[data-k], button[data-cmd], button[data-scroll], button[data-open]").forEach(btn => {
    let delay, repeat;
    const fire = () => send(command(btn));
    const stop = () => { clearTimeout(delay); clearInterval(repeat); btn.classList.remove("on"); };
    onPress(btn, e => {
      fire();
      if (e.type !== "pointerdown") return;   // a keyboard or screen reader click: nothing is being held down
      e.preventDefault();
      btn.classList.add("on");
      if (btn.hasAttribute("data-repeat")) delay = setTimeout(() => { repeat = setInterval(fire, 130); }, 400);
    });
    ["pointerup", "pointercancel", "pointerleave"].forEach(t => btn.addEventListener(t, stop));
  });
}
