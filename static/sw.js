const CACHE_NAME = "tareas-sheets-v1";
const OFFLINE_URL = "/offline";
const ASSETS = [
  "/",
  "/static/manifest.webmanifest",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (e) => {
  const { request } = e;
  // Estrategia: Network first, fallback a cache y offline.
  e.respondWith(
    fetch(request)
      .then((res) => {
        const resClone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, resClone));
        return res;
      })
      .catch(async () => {
        const cache = await caches.open(CACHE_NAME);
        const cached = await cache.match(request);
        return cached || cache.match(OFFLINE_URL) || new Response("Offline", { status: 503 });
      })
  );
});
