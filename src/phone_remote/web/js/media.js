// 播放状态：定时问电脑，更新播放键、标题、进度条和音量。
// 浏览器上报“播放 / 暂停”可能晚十秒左右，所以按下播放键后先按预期显示，过一会儿再以电脑为准。
import { send, token } from "./api.js";
import { commands } from "./buttons.js";
import { t } from "./i18n.js";

const playButtons = document.querySelectorAll(".playbtn");
const nowCard = document.getElementById("nowcard");
const nowBox = document.getElementById("now"), volBox = document.getElementById("vol");
const nowTitle = document.getElementById("nowtitle"), nowApp = document.getElementById("nowapp");
const kindIcon = document.getElementById("nowkind");
const KINDS = { music: { icon: "music", label: "Music" }, video: { icon: "movie", label: "Video" } };
const curBox = document.getElementById("cur"), totalBox = document.getElementById("total");
const track = document.getElementById("track"), fill = document.getElementById("fill"), knob = document.getElementById("knob");
// rate is how fast the position moves while playing: 0 when the video is stuck loading
const media = { playing: null, title: "", pos: 0, dur: 0, rate: 1, at: 0, holdPlay: 0, holdPos: 0, serverPos: 0 };
const stateListeners = [];
let dragging = null;

// 每次从电脑拿到状态后通知（定时暂停用它显示剩余时间）
export function onState(fn) { stateListeners.push(fn); }

function clock(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = String(sec % 60).padStart(2, "0");
  return h ? h + ":" + String(m).padStart(2, "0") + ":" + s : m + ":" + s;
}
function localPos() {
  const pos = media.playing ? media.pos + (performance.now() - media.at) / 1000 * media.rate : media.pos;
  return Math.max(0, Math.min(media.dur, pos));
}
function setPos(pos) { media.pos = pos; media.at = performance.now(); }

function render() {
  const name = media.playing === true ? "playing" : media.playing === false ? "paused" : "unknown";
  playButtons.forEach(b => { b.dataset.state = name; });
  const hasTitle = media.playing !== null && media.title;
  nowTitle.textContent = hasTitle ? media.title : "";
  if (hasTitle && media.artist) {
    const artist = document.createElement("span");
    artist.textContent = " · " + media.artist;
    nowTitle.appendChild(artist);
  }
  nowApp.textContent = hasTitle ? media.app : "";
  const kind = hasTitle && KINDS[media.kind];
  kindIcon.toggleAttribute("hidden", !kind);   // an <svg> has no .hidden property, only the attribute
  if (kind) {
    // Only when it changes: setting href again, even to the same value, makes the browser fetch
    // icons.svg again, and the icon blinks while that is on its way
    const href = "icons.svg#" + kind.icon;
    if (kindIcon.firstChild.getAttribute("href") !== href) kindIcon.firstChild.setAttribute("href", href);
    kindIcon.setAttribute("aria-label", t(kind.label));
  }
  nowBox.classList.toggle("paused", media.playing === false);
  nowCard.hidden = !((hasTitle && nowBox.isConnected) || (media.dur && track.isConnected));
  document.body.classList.toggle("notimeline", !media.dur);
  if (media.dur) {
    const pos = dragging === null ? localPos() : dragging;
    const percent = pos / media.dur * 100 + "%";
    fill.style.width = percent; knob.style.left = percent;
    curBox.textContent = clock(pos); totalBox.textContent = clock(media.dur);
  }
}

function applyState(state) {
  const now = performance.now();
  const newVideo = state.dur !== media.dur || state.title !== media.title;
  const moved = Math.abs(state.pos - media.serverPos) > 2;   // 电脑上的进度跳了，说明发生过跳转
  media.serverPos = state.pos;
  const rate = state.rate === undefined ? 1 : state.rate;   // an older computer does not send it
  if (rate !== media.rate) { setPos(now > media.holdPos ? state.pos : localPos()); media.rate = rate; }
  if (newVideo || now > media.holdPlay || media.playing === null || state.playing === null) {
    if (state.playing !== media.playing) { setPos(localPos()); media.playing = state.playing; }
  }
  media.dur = state.dur || 0;
  media.title = state.title || "";
  media.artist = state.artist || "";
  media.kind = state.kind || "";
  media.app = state.app || "";
  if (newVideo) setPos(state.pos);
  else if (now > media.holdPos && Math.abs(state.pos - localPos()) > 2 && (moved || state.playing === media.playing)) setPos(state.pos);
  volBox.textContent = state.vol === null || state.vol === undefined ? "" : state.muted ? t("Muted") : t("Volume {n}", { n: state.vol });
  stateListeners.forEach(fn => fn(state));
  render();
}

export function pollState() {
  if (document.hidden || !token) return;
  send({ a: "state" }).then(state => { if (state && typeof state === "object") applyState(state); });
}

// 跳转：进度条拖动和 ±30 秒都换算成绝对位置发给电脑
function seekTo(pos) {
  if (!media.dur) return;
  pos = Math.max(0, Math.min(media.dur - 1, pos));
  setPos(pos);
  media.holdPos = performance.now() + 2500;
  send({ a: "seek", to: pos });
  render();
}
function trackPos(e) {
  const box = track.getBoundingClientRect();
  return Math.max(0, Math.min(1, (e.clientX - box.left) / box.width)) * media.dur;
}

export function initMedia() {
  setInterval(pollState, 1500);
  setInterval(render, 500);
  document.addEventListener("visibilitychange", pollState);
  pollState();

  // The play button says which way to go and what this page is showing, so that a second press, or
  // one sent before the next poll, cannot start something else that has become current on the computer
  commands.playpause = () => {
    if (media.playing === null) return { a: "playpause" };
    const msg = { a: "playpause", play: !media.playing, title: media.title };
    setPos(localPos());
    media.playing = !media.playing;
    media.holdPlay = performance.now() + 12000;
    render();
    return msg;
  };

  track.addEventListener("pointerdown", e => { track.setPointerCapture(e.pointerId); dragging = trackPos(e); render(); });
  track.addEventListener("pointermove", e => { if (dragging !== null) { dragging = trackPos(e); render(); } });
  track.addEventListener("pointerup", e => { if (dragging !== null) { const pos = trackPos(e); dragging = null; seekTo(pos); } });
  track.addEventListener("pointercancel", () => { dragging = null; render(); });
  document.querySelectorAll("button[data-rel]").forEach(b => {
    b.addEventListener("pointerdown", () => { b.classList.add("on"); seekTo(localPos() + Number(b.dataset.rel)); });
    ["pointerup", "pointercancel", "pointerleave"].forEach(t => b.addEventListener(t, () => b.classList.remove("on")));
  });
}
