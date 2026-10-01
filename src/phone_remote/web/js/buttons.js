// 通用按钮：按下立即触发，带 data-repeat 的长按连发
import { env, send } from "./api.js";

function command(btn) {
  if (btn.dataset.scroll) return { a: "scroll", dy: Number(btn.dataset.scroll) };
  if (btn.dataset.open) return { a: "open", url: btn.dataset.open };
  return { a: "key", k: (env.platform === "mac" && btn.dataset.mac) || btn.dataset.k };
}

export function initButtons() {
  document.querySelectorAll("button[data-k], button[data-scroll], button[data-open]").forEach(btn => {
    let delay, repeat;
    const fire = () => send(command(btn));
    const stop = () => { clearTimeout(delay); clearInterval(repeat); btn.classList.remove("on"); };
    btn.addEventListener("pointerdown", e => {
      e.preventDefault();
      btn.classList.add("on");
      fire();
      if (btn.hasAttribute("data-repeat")) delay = setTimeout(() => { repeat = setInterval(fire, 130); }, 400);
    });
    ["pointerup", "pointercancel", "pointerleave"].forEach(t => btn.addEventListener(t, stop));
    btn.addEventListener("contextmenu", e => e.preventDefault());
  });
}
