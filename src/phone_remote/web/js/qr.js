// Reads the QR code in a photo. A web page may only use the camera live over HTTPS, which a program on a
// home network cannot offer, but it may always ask for one photo; so the code is photographed, then read here.

// The reader (vendor/jsQR.js, Apache License 2.0) is large and rarely needed, so it is fetched on first use
let reader;
function loadReader() {
  reader = reader || new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "vendor/jsQR.js";
    script.onload = () => resolve(window.jsQR);
    script.onerror = () => { reader = null; reject(new Error("reader not loaded")); };
    document.head.appendChild(script);
  });
  return reader;
}

// A phone photo is far larger than needed, and a smaller picture also blurs away the pattern a screen's pixels
// leave in it. The larger size is a second try, for a code that takes up only a small part of the photo.
const SIZES = [1000, 2000];

// Resolves to the text of the QR code in an image file, or null when none can be made out
export async function readQr(file) {
  const [jsQR, image] = await Promise.all([loadReader(), loadImage(file)]);
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", { willReadFrequently: true });
  for (const size of SIZES) {
    const scale = Math.min(1, size / Math.max(image.naturalWidth, image.naturalHeight));
    canvas.width = Math.round(image.naturalWidth * scale);
    canvas.height = Math.round(image.naturalHeight * scale);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const found = jsQR(context.getImageData(0, 0, canvas.width, canvas.height).data, canvas.width, canvas.height);
    if (found && found.data) return found.data;
    if (scale === 1) break;   // the photo was not shrunk, so a larger size would be the same picture
  }
  return null;
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const image = new Image(), address = URL.createObjectURL(file);
    image.onload = () => { URL.revokeObjectURL(address); resolve(image); };
    image.onerror = () => { URL.revokeObjectURL(address); reject(new Error("not a picture")); };
    image.src = address;
  });
}
