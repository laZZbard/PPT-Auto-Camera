const C='ppt-auto-camera-v2';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>{
 self.skipWaiting();
 e.waitUntil(caches.open(C).then(c=>c.addAll(ASSETS)));
});
self.addEventListener('activate',e=>e.waitUntil(
 caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==C).map(k=>caches.delete(k))))
  .then(()=>self.clients.claim())
));
self.addEventListener('fetch',e=>e.respondWith(
 fetch(e.request).then(r=>{
  const copy=r.clone();
  caches.open(C).then(c=>c.put(e.request,copy));
  return r;
 }).catch(()=>caches.match(e.request))
));
