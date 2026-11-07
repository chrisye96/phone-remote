// Small values remembered in the browser; quietly does nothing where storage is unavailable
export const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  all() { try { return { ...localStorage }; } catch (e) { return {}; } },
};

// What is remembered belongs to one address, so a move to the computer's name (stable.js) brings it along
// after the #, which never reaches the network. Anything already remembered at this address stays.
const [own, carried] = location.hash.split("&carry=");
if (carried !== undefined) {
  history.replaceState(null, "", own);
  try {
    const values = JSON.parse(decodeURIComponent(carried));
    for (const key in values) if (store.get(key) === null) store.set(key, values[key]);
  } catch (e) {}
}
