// Computer switcher in the header: pick a paired computer, add another one, rename or remove the current one
import { active, addDevice, devices, parseDevice, removeDevice, renameActive, switchDevice } from "./api.js";
import { t } from "./i18n.js";

const select = document.getElementById("device");
const sheet = document.getElementById("devsheet"), form = document.getElementById("devform");
const title = document.getElementById("devtitle"), addFields = document.getElementById("devadd");
const urlInput = document.getElementById("devurl"), nameInput = document.getElementById("devname");
const error = document.getElementById("deverror"), saveButton = document.getElementById("devsave");
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
  (add ? urlInput : nameInput).focus();
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
