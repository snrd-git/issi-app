// Service worker: aplikasi tetap jalan offline; data diambil dari jaringan bila online.
const VER = "issi-v2";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icon.svg", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VER).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  const key = url.origin + url.pathname;              // abaikan ?t=… saat menyimpan
  if (url.pathname.includes("/data/")) {
    // data: jaringan dulu, cadangan cache
    e.respondWith(fetch(e.request).then(r => {
      if (r.ok) { const cp = r.clone(); caches.open(VER).then(c => c.put(key, cp)); }
      return r;
    }).catch(() => caches.match(key)));
  } else {
    // aplikasi: cache dulu, perbarui di belakang
    e.respondWith(caches.match(key).then(hit => {
      const net = fetch(e.request).then(r => {
        if (r.ok) { const cp = r.clone(); caches.open(VER).then(c => c.put(key, cp)); }
        return r;
      }).catch(() => hit);
      return hit || net;
    }));
  }
});
