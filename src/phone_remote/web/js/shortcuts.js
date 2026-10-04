// 常用网页：点一下在电脑上打开，长按修改或删除，最后一格是“添加”
import { send } from "./api.js";
import { t } from "./i18n.js";
import { toast } from "./status.js";

// The Browse screen has the row of shortcuts; on a tablet the Play screen shows the same row
const boxes = document.querySelectorAll(".shortcuts");
const sheet = document.getElementById("sheet"), form = document.getElementById("sheetform");
const title = document.getElementById("sheettitle"), error = document.getElementById("sheeterror");
const urlInput = document.getElementById("sheeturl"), nameInput = document.getElementById("sheetname");
const saveButton = document.getElementById("sheetsave"), deleteButton = document.getElementById("sheetdelete");
const LONG_PRESS = 550;
let shortcuts = [], max = 4, editing = null;   // editing：正在改第几个，null 表示新增

function openSheet(index) {
  editing = index;
  const item = index === null ? { url: "", name: "" } : shortcuts[index];
  title.textContent = index === null ? t("Add shortcut") : t("Edit shortcut");
  urlInput.value = item.url;
  nameInput.value = item.name;
  error.textContent = "";
  deleteButton.hidden = index === null;
  sheet.hidden = false;
  if (index === null) urlInput.focus();
}
function closeSheet() {
  sheet.hidden = true;
  document.activeElement && document.activeElement.blur();
}

function tile(item, index) {
  const btn = document.createElement("button");
  btn.className = "shortcut";
  btn.style.setProperty("--site", item.color);
  btn.appendChild(document.createElement("em"));
  btn.appendChild(document.createTextNode(item.name));
  let timer = null, held = false;
  btn.addEventListener("pointerdown", () => {
    held = false;
    btn.classList.add("on");
    timer = setTimeout(() => { held = true; btn.classList.remove("on"); openSheet(index); }, LONG_PRESS);
  });
  btn.addEventListener("pointerup", () => {
    clearTimeout(timer);
    btn.classList.remove("on");
    if (!held) send({ a: "open", i: index }).then(ok => { if (ok) toast(t("Opened {name} on the computer", { name: item.name })); });
  });
  ["pointercancel", "pointerleave"].forEach(t => btn.addEventListener(t, () => { clearTimeout(timer); btn.classList.remove("on"); }));
  btn.addEventListener("contextmenu", e => e.preventDefault());
  return btn;
}

export function renderShortcuts(list, limit) {
  shortcuts = list;
  if (limit) max = limit;
  boxes.forEach(box => {
    box.textContent = "";
    list.forEach((item, index) => box.appendChild(tile(item, index)));
    if (list.length < max) {
      const add = document.createElement("button");
      add.className = "shortcut add";
      add.textContent = t("+ Add");
      add.addEventListener("click", () => openSheet(null));
      box.appendChild(add);
    }
  });
}

export function initShortcuts() {
  form.addEventListener("submit", e => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) { error.textContent = t("Enter an address first"); return; }
    const message = { a: "shortcut_save", url, name: nameInput.value.trim() };
    if (editing !== null) message.i = editing;
    saveButton.disabled = true;
    saveButton.textContent = t("Reading the page…");
    send(message).then(list => {
      saveButton.disabled = false;
      saveButton.textContent = t("Save");
      if (Array.isArray(list)) { renderShortcuts(list); closeSheet(); }
      else error.textContent = t("Can't save: the address should look like bilibili.com or https://…");
    });
  });
  deleteButton.addEventListener("click", () => {
    send({ a: "shortcut_delete", i: editing }).then(list => { if (Array.isArray(list)) { renderShortcuts(list); closeSheet(); } });
  });
  document.getElementById("sheetcancel").addEventListener("click", closeSheet);
  sheet.addEventListener("pointerdown", e => { if (e.target === sheet) closeSheet(); });
}
