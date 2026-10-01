// 触控板：播放、浏览、输入页各有一块，共用一套手势。
// 单指滑动移动鼠标，轻点单击；双指滑动滚动，双指轻点右键。
import { send } from "./api.js";

const SPEED = 1.7;
const pending = { dx: 0, dy: 0, scroll: 0 };
let busy = false;

// 把攒下的移动量发出去；上一条还没回来就先攒着，避免堆积
function flush() {
  if (busy) return;
  const dx = Math.round(pending.dx), dy = Math.round(pending.dy), scroll = Math.round(pending.scroll);
  if (!dx && !dy && !scroll) return;
  pending.dx -= dx; pending.dy -= dy; pending.scroll -= scroll;
  busy = true;
  const jobs = [];
  if (dx || dy) jobs.push(send({ a: "move", dx, dy }));
  if (scroll) jobs.push(send({ a: "scroll", dy: scroll }));
  Promise.all(jobs).then(() => { busy = false; flush(); });
}

function initPad(pad) {
  const pointers = new Map();
  let travel = 0, startTime = 0, maxPointers = 0;
  pad.addEventListener("pointerdown", e => {
    pad.setPointerCapture(e.pointerId);
    if (pointers.size === 0) { travel = 0; startTime = Date.now(); maxPointers = 0; }
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    maxPointers = Math.max(maxPointers, pointers.size);
    pad.classList.add("on");
  });
  pad.addEventListener("pointermove", e => {
    const last = pointers.get(e.pointerId);
    if (!last) return;
    const dx = e.clientX - last.x, dy = e.clientY - last.y;
    last.x = e.clientX; last.y = e.clientY;
    travel += Math.abs(dx) + Math.abs(dy);
    if (pointers.size === 1) { pending.dx += dx * SPEED; pending.dy += dy * SPEED; }
    else pending.scroll += dy / pointers.size * 2.5;
    flush();
  });
  function padUp(e) {
    if (!pointers.delete(e.pointerId) || pointers.size) return;
    pad.classList.remove("on");
    const quick = e.type === "pointerup" && Date.now() - startTime < 300;
    if (quick && maxPointers === 1 && travel < 8) send({ a: "click" });
    else if (quick && maxPointers === 2 && travel < 16) send({ a: "click", right: true });
  }
  pad.addEventListener("pointerup", padUp);
  pad.addEventListener("pointercancel", padUp);
}

export function initTouchpads() {
  document.querySelectorAll(".pad").forEach(initPad);
}
