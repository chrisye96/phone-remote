// How buttons are pressed and marked, shared by every part of the page. No imports, so tests can run it alone.

const CLICK_AFTER_PRESS_MS = 700;   // a click this soon after a finger went down or came up belongs to that finger

// Runs fn the moment a finger or mouse goes down, without waiting for it to come up. A keyboard, a switch
// or a screen reader sends only a click, with no press before it, so such a click runs fn too.
export function onPress(el, fn) {
  let pressed = -Infinity;   // when a pointer last went down or came up on el
  el.addEventListener("pointerdown", e => { pressed = e.timeStamp; fn(e); });
  el.addEventListener("pointerup", e => { pressed = e.timeStamp; });
  el.addEventListener("click", e => { if (e.timeStamp - pressed > CLICK_AFTER_PRESS_MS) fn(e); });
}

// Marks which of a set of buttons is the chosen one, for the eye (class sel) and for a screen reader
export function choose(buttons, attr, value) {
  buttons.forEach(b => {
    const on = b.dataset[attr] === value;
    b.classList.toggle("sel", on);
    b.setAttribute("aria-pressed", on);
  });
}
