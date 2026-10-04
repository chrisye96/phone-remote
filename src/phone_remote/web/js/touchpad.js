// Touchpad: the Play, Browse and Type screens each have one, all with the same gestures.
// One finger: slide to move the pointer, tap to click, hold still then slide to drag.
// Two fingers: slide to scroll (it coasts after a quick flick), tap to right-click.
import { send } from "./api.js";

const SPEED = 1.7;
const HOLD_MS = 400;          // how long a finger must rest before the mouse button goes down
const HOLD_SLACK = 8;         // movement, in pixels, that still counts as resting
const HOLD_REPEAT_MS = 1000;  // the computer lets go by itself if it stops hearing this
const COAST_DECAY = 0.997;    // share of the scroll speed kept each millisecond after a flick
const COAST_MIN = 0.25;       // release speed, in scroll units per millisecond, needed to coast at all
const COAST_STOP = 0.03;
const FLICK_WINDOW = 100;     // milliseconds of scrolling looked at to measure that speed
const pending = { dx: 0, dy: 0, scroll: 0 };
let busy = false;
let coasting = 0;             // timer of the scroll that keeps going after a flick

// Sends what has built up. While the last send is still out, more builds up instead of queueing behind it.
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

function stopCoasting() { clearInterval(coasting); coasting = 0; }

// Keeps scrolling at the speed the fingers left with, slowing down until it stops
function coast(speed) {
  let last = performance.now();
  coasting = setInterval(() => {
    const now = performance.now(), dt = Math.min(now - last, 50);
    last = now;
    pending.scroll += speed * dt;
    speed *= Math.pow(COAST_DECAY, dt);
    flush();
    if (Math.abs(speed) < COAST_STOP) stopCoasting();
  }, 16);
}

function initPad(pad) {
  const pointers = new Map();
  let travel = 0, startTime = 0, maxPointers = 0;
  let holdTimer = 0, holdRepeat = 0, holding = false;
  const recent = [];   // [time, amount] of two-finger scrolling over the last FLICK_WINDOW milliseconds

  // Scroll speed at the moment the fingers left, in scroll units per millisecond; 0 if they had already stopped
  function flickSpeed() {
    const now = performance.now();
    const fresh = recent.filter(([time]) => now - time <= FLICK_WINDOW);
    if (!fresh.length || now - fresh[fresh.length - 1][0] > 60) return 0;
    return fresh.reduce((sum, [, amount]) => sum + amount, 0) / Math.max(now - fresh[0][0], 16);
  }

  const cancelHold = () => { clearTimeout(holdTimer); holdTimer = 0; };
  function startHold() {
    holdTimer = 0;
    holding = true;
    pad.classList.add("hold");
    send({ a: "button", down: true });
    holdRepeat = setInterval(() => send({ a: "button", down: true }), HOLD_REPEAT_MS);
  }
  function endHold() {
    clearInterval(holdRepeat);
    holding = false;
    pad.classList.remove("hold");
    send({ a: "button", down: false });
  }

  pad.addEventListener("pointerdown", e => {
    pad.setPointerCapture(e.pointerId);
    stopCoasting();   // touching the pad stops a coasting scroll, like putting a finger on a moving page
    if (pointers.size === 0) {
      travel = 0; startTime = Date.now(); maxPointers = 0; recent.length = 0;
      holdTimer = setTimeout(startHold, HOLD_MS);
    } else cancelHold();   // a second finger means scrolling or a right-click, not a drag
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
    if (travel > HOLD_SLACK) cancelHold();
    if (pointers.size === 1) {
      // After a two-finger gesture the fingers rarely lift together; the one left behind must not nudge the pointer
      if (maxPointers === 1) { pending.dx += dx * SPEED; pending.dy += dy * SPEED; }
    } else {
      const amount = dy / pointers.size * 2.5;
      pending.scroll += amount;
      const now = performance.now();
      recent.push([now, amount]);
      while (now - recent[0][0] > FLICK_WINDOW) recent.shift();
    }
    flush();
  });
  function padUp(e) {
    if (!pointers.delete(e.pointerId)) return;
    if (pointers.size) return;
    cancelHold();
    pad.classList.remove("on");
    if (holding) return endHold();
    const quick = e.type === "pointerup" && Date.now() - startTime < 300;
    if (quick && maxPointers === 1 && travel < 8) send({ a: "click" });
    else if (quick && maxPointers === 2 && travel < 16) send({ a: "click", right: true });
    else if (maxPointers === 2) {
      const speed = flickSpeed();
      if (Math.abs(speed) > COAST_MIN) coast(speed);
    }
  }
  pad.addEventListener("pointerup", padUp);
  pad.addEventListener("pointercancel", padUp);
}

export function initTouchpads() {
  document.querySelectorAll(".pad").forEach(initPad);
}
