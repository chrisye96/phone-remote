// QR page on the computer: one click on the address or its icon copies it, and the icon turns into a tick for a moment.
// The page is only ever opened as http://127.0.0.1, which browsers treat as secure, so the clipboard is available.
const button = document.getElementById("copy");
const icon = button.querySelector("use");
let timer;

button.addEventListener("click", () => {
  navigator.clipboard.writeText(button.querySelector("code").textContent).then(() => {
    icon.setAttribute("href", "/icons.svg#check");
    button.classList.add("done");
    clearTimeout(timer);
    timer = setTimeout(() => { icon.setAttribute("href", "/icons.svg#copy"); button.classList.remove("done"); }, 1500);
  });
});
