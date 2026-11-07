// The router can give the computer a new IP address, and a home screen icon keeps the address it was added with.
// The computer's name stays the same, so the phone moves to the name as soon as it finds that the name works.
import { active, devices, moveActive, proves, token } from "./api.js";
import { renderDevices } from "./devices.js";
import { store } from "./store.js";

const ipAddress = /^(?!127\.)\d+\.\d+\.\d+\.\d+$/;   // on the computer itself, the name would gain nothing

// The new address, with what is remembered at this one rewritten to match it
function carryingTo(url) {
  const values = store.all();
  values.active = url;
  values.devices = JSON.stringify(devices.filter(d => d === active || d.url !== url).map(d => (d === active ? { ...d, url } : d)));
  return url + "/#" + token + "&carry=" + encodeURIComponent(JSON.stringify(values));
}

// A page cannot change the address inside its own home screen icon, so this one takes the person's hand, once
function offerNewIcon(url) {
  const sheet = document.getElementById("stablesheet"), link = document.getElementById("stablelink");
  link.href = carryingTo(url);
  [link, document.getElementById("stablelater")].forEach(el => el.addEventListener("click", () => { sheet.hidden = true; }));
  sheet.hidden = false;
  store.set("stablehint", "1");
}

export function settleAddress(local) {
  const address = new URL(active.url);
  const servedHere = active.url === location.origin;
  const icon = navigator.standalone || matchMedia("(display-mode: standalone)").matches;
  if (!local || !ipAddress.test(address.hostname) || (servedHere && icon && store.get("stablehint"))) return Promise.resolve();
  const stable = address.origin.replace(address.hostname, local);
  return proves(stable).then(proved => {
    if (!proved) return;
    if (!servedHere) { moveActive(stable); renderDevices(); }   // this page keeps running; only commands go elsewhere
    else if (icon) offerNewIcon(stable);
    else location.replace(carryingTo(stable));   // before anyone adds an icon, so the icon gets the name
  });
}
