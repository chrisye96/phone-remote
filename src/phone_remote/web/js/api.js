// 和电脑通信：配对码、发指令
import { setStatus } from "./status.js";

export const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};

export const token = location.hash.slice(1) || store.get("token") || "";
if (token) store.set("token", token);

// 电脑的信息，连上后由 main.js 填入
export const env = { platform: "win" };

// 发指令给电脑；成功返回 true（有数据时返回数据），失败返回 false
export function send(data) {
  if (!token) { setStatus(false, "还没配对：请扫电脑上的二维码打开"); return Promise.resolve(false); }
  return fetch("/api", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Token": token },
    body: JSON.stringify(data),
  }).then(r => {
    if (r.status === 403) setStatus(false, "配对失效：请重新扫电脑上的二维码");
    else setStatus(true);
    if (!r.ok) return false;
    return r.status === 200 ? r.json() : true;
  }).catch(() => { setStatus(false, "连不上电脑：检查程序是否开着、是否同一个 Wi-Fi"); return false; });
}
