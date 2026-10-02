// Talking to the computer: paired computers, pairing tokens, sending commands
import { hmacSha256 } from "./hmac.js";
import { t } from "./i18n.js";
import { setStatus } from "./status.js";
import { store } from "./store.js";

export { store };

// Turns "http://192.168.1.5:8765/#token" (the address on a QR page) into { url, token }; null if it is not one
export function parseDevice(text) {
  try {
    const u = new URL(/^https?:\/\//i.test(text) ? text : "http://" + text);
    const token = u.hash.slice(1);
    return token && u.hostname ? { url: u.origin, token } : null;
  } catch (e) { return null; }
}

// Paired computers: [{ url, token, name, alias }]; name is what the computer calls itself, alias what the user typed. This page is served by one of them, commands go to the active one.
export let devices = [];
try { devices = JSON.parse(store.get("devices")) || []; } catch (e) {}
function saveDevices() { store.set("devices", JSON.stringify(devices)); }

// Adds or updates a computer; returns it only when something changed
function upsert(found) {
  const known = devices.find(d => d.url === found.url);
  if (known && known.token === found.token) return null;
  if (known) known.token = found.token; else devices.push(known || found);
  saveDevices();
  return known || found;
}

// The address this page was opened with pairs the computer serving it. It only becomes the active one
// when it is new, because a home screen icon keeps its #token and would undo every switch otherwise.
const legacyToken = store.get("token");   // before multiple computers, the only token lived here
const own = parseDevice(location.href) || (legacyToken && !devices.length ? { url: location.origin, token: legacyToken } : null);
const fresh = own && upsert(own);
if (fresh) store.set("active", fresh.url);

export const active = devices.find(d => d.url === store.get("active")) || devices[0] || null;
export const token = active ? active.token : "";

export function switchDevice(url) { store.set("active", url); location.reload(); }
export function addDevice(found, alias) {
  const device = upsert(found);
  if (alias) { device.alias = alias; saveDevices(); }
  switchDevice(found.url);
}
export function renameActive(alias) { active.alias = alias; saveDevices(); }
export function removeDevice(url) {
  devices = devices.filter(d => d.url !== url);
  saveDevices();
  location.reload();
}
// Remembers the computer's own name once it has answered
export function nameActive(name) { if (active && name && active.name !== name) { active.name = name; saveDevices(); } }

// Info about the computer, filled in by main.js after connecting
export const env = { platform: "win" };

// Sends a command to the computer; resolves to true on success (or the data when there is some), false on failure
let clockOffset = 0;   // the computer's clock minus ours, learned when it turns a command down as stale
let lastSent = 0;
let refused = "";      // set once the computer rejects our signature; trying again would only get this phone locked out

// The token is never sent. Each command carries the time and a signature over time and body,
// so someone listening on the network can neither learn the token nor replay what they heard.
function post(body) {
  const sent = lastSent = Math.max(Date.now() + clockOffset, lastSent + 1);   // never the same twice
  return fetch(active.url + "/api", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Auth": sent + "." + hmacSha256(token, sent + "\n" + body) },
    body,
  });
}

export function send(data) {
  if (!token) { setStatus(false, t("Not paired yet: scan the QR code on the computer")); return Promise.resolve(false); }
  if (refused) { setStatus(false, refused); return Promise.resolve(false); }
  const body = JSON.stringify(data);
  return post(body).then(r => {
    if (r.status !== 401) return r;
    // Our clock and the computer's disagree: adopt its time and try once more
    return r.json().then(info => { clockOffset = info.now - Date.now(); lastSent = 0; return post(body); });
  }).then(r => {
    if (r.status === 403) setStatus(false, refused = t("Pairing no longer valid: scan the QR code on the computer again"));
    else if (r.status === 429) setStatus(false, t("Too many failed attempts: the computer ignores this device for 5 minutes"));
    else if (r.status === 401) setStatus(false, t("Clocks don't match: reopen this page"));
    else setStatus(true);
    if (!r.ok) return false;
    return r.status === 200 ? r.json() : true;
  }).catch(() => { setStatus(false, t("Can't reach the computer: check that the program is running and both are on the same Wi-Fi")); return false; });
}
