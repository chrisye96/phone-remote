// HMAC-SHA256 written out by hand: the browser's own crypto.subtle only exists on HTTPS pages,
// and this page is served over plain HTTP on the local network.
// Checked against Python's hmac module in tests/test_hmac_js.py.

// SHA-256 constants: the fractional parts of the square and cube roots of the first primes
const K = new Uint32Array(64), H0 = new Uint32Array(8);
for (let n = 2, found = 0; found < 64; n++) {
  let prime = true;
  for (let d = 2; d * d <= n; d++) if (n % d === 0) { prime = false; break; }
  if (!prime) continue;
  if (found < 8) H0[found] = (Math.sqrt(n) % 1) * 0x100000000;
  K[found++] = (Math.cbrt(n) % 1) * 0x100000000;
}

const rotr = (x, n) => (x >>> n) | (x << (32 - n));

function sha256(bytes) {
  const padded = new Uint8Array(((bytes.length + 9 + 63) >> 6) << 6);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(padded.length - 8, Math.floor(bytes.length / 0x20000000));
  view.setUint32(padded.length - 4, bytes.length * 8 >>> 0);
  const h = H0.slice(), w = new Uint32Array(64);
  for (let block = 0; block < padded.length; block += 64) {
    for (let i = 0; i < 16; i++) w[i] = view.getUint32(block + i * 4);
    for (let i = 16; i < 64; i++) {
      const x = w[i - 15], y = w[i - 2];
      w[i] = w[i - 16] + (rotr(x, 7) ^ rotr(x, 18) ^ (x >>> 3)) + w[i - 7] + (rotr(y, 17) ^ rotr(y, 19) ^ (y >>> 10));
    }
    let [a, b, c, d, e, f, g, k] = h;
    for (let i = 0; i < 64; i++) {
      const t1 = (k + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) | 0;
      const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
      k = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    [a, b, c, d, e, f, g, k].forEach((value, i) => { h[i] += value; });
  }
  const out = new Uint8Array(32), outView = new DataView(out.buffer);
  h.forEach((value, i) => outView.setUint32(i * 4, value));
  return out;
}

function concat(a, b) {
  const joined = new Uint8Array(a.length + b.length);
  joined.set(a); joined.set(b, a.length);
  return joined;
}

// Both arguments are strings; the result is lowercase hex, the same as Python's hmac hexdigest()
export function hmacSha256(key, message) {
  const encoder = new TextEncoder();
  let keyBytes = encoder.encode(key);
  if (keyBytes.length > 64) keyBytes = sha256(keyBytes);
  const inner = new Uint8Array(64).fill(0x36), outer = new Uint8Array(64).fill(0x5c);
  keyBytes.forEach((byte, i) => { inner[i] ^= byte; outer[i] ^= byte; });
  const digest = sha256(concat(outer, sha256(concat(inner, encoder.encode(message)))));
  return Array.from(digest, byte => byte.toString(16).padStart(2, "0")).join("");
}
