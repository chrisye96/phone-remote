// Computer switcher in the header: pick a paired computer, add another one, rename or remove the current one
import { active, addDevice, devices, parseDevice, removeDevice, renameActive, switchDevice } from "./api.js";
import { t } from "./i18n.js";
import { readQr } from "./qr.js";

const select = document.getElementById("device");
const sheet = document.getElementById("devsheet"), form = document.getElementById("devform");
const title = document.getElementById("devtitle"), addFields = document.getElementById("devadd");
const urlInput = document.getElementById("devurl"), nameInput = document.getElementById("devname");
const error = document.getElementById("deverror"), saveButton = document.getElementById("devsave");
const photoButton = document.getElementById("devphoto"), photoInput = document.getElementById("devfile");
let adding = false;   // the sheet either adds a computer or renames the active one

// The name the user gave, else the computer's own name, else its address
export function label(d) { return d.alias || d.name || d.url.replace(/^https?:\/\//, ""); }

export function renderDevices() {
  select.textContent = "";
  const option = (value, text) => select.add(new Option(text, value));
  if (!devices.length) option("", t("Not paired"));
  devices.forEach(d => option(d.url, label(d)));
  option("+", t("Add computer…"));
  if (active) option("=", t("Rename {name}…", { name: label(active) }));
  if (devices.length > 1) option("-", t("Remove {name}", { name: label(active) }));
  select.value = active ? active.url : "";
}

function openSheet(add) {
  adding = add;
  title.textContent = add ? t("Add computer") : t("Rename this computer");
  addFields.hidden = !add;
  urlInput.value = error.textContent = "";
  nameInput.value = add ? "" : active.alias || "";
  saveButton.textContent = add ? t("Add and switch") : t("Save");
  saveButton.disabled = add;
  sheet.hidden = false;
  (add ? photoButton : nameInput).focus();   // not the address box: that would cover the photo button with the on-screen keyboard
}
function closeSheet() {
  sheet.hidden = true;
  document.activeElement && document.activeElement.blur();
}

export function initDevices() {
  renderDevices();
  select.addEventListener("change", () => {
    const choice = select.value;
    select.value = active ? active.url : "";
    if (choice === "+" || choice === "=") openSheet(choice === "+");
    else if (choice === "-") { if (confirm(t("Remove {name}? You will have to add it again to use it.", { name: label(active) }))) removeDevice(active.url); }
    else if (choice) switchDevice(choice);
  });
  urlInput.addEventListener("input", () => { error.textContent = ""; saveButton.disabled = !urlInput.value.trim(); });
  // The photo fills in the address box, as if it had been typed, and the rest of the sheet carries on from there
  photoButton.addEventListener("click", () => photoInput.click());
  photoInput.addEventListener("change", () => {
    const file = photoInput.files[0];
    photoInput.value = "";   // so that taking the same photo again still counts as a change
    if (!file) return;
    error.textContent = "";
    photoButton.disabled = true;
    photoButton.textContent = t("Reading the photo…");
    readQr(file).catch(() => null).then(text => {
      photoButton.disabled = false;
      photoButton.textContent = t("Take a photo of its QR code");
      if (!text) error.textContent = t("No QR code found in the photo: move closer so the code fills most of it, and try again");
      else if (!parseDevice(text)) error.textContent = t("That QR code is not from a Phone Remote QR page");
      else { urlInput.value = text; saveButton.disabled = false; }
    });
  });
  form.addEventListener("submit", e => {
    e.preventDefault();
    const alias = nameInput.value.trim();
    if (!adding) { renameActive(alias); renderDevices(); return closeSheet(); }
    const found = parseDevice(urlInput.value.trim());
    if (!found) error.textContent = t("Incomplete address: it should look like 192.168.1.5:8765/#code, including the part after #");
    else if (devices.some(d => d.url === found.url && d.token === found.token)) error.textContent = t("This computer is already added");
    else addDevice(found, alias);
  });
  document.getElementById("devcancel").addEventListener("click", closeSheet);
  sheet.addEventListener("pointerdown", e => { if (e.target === sheet) closeSheet(); });
}
