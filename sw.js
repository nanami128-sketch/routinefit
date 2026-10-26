/* RoutineFit v1.2.0 – network-first navigation, offline fallback, no data deletion. */
const CACHE = 'routinefit-v1.2.0-core';
const CORE = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('routinefit-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request=event.request;
  const url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin) return;
  if(request.mode==='navigate'||request.destination==='document'){
    event.respondWith((async()=>{
      try {
        const response=await fetch(request,{cache:'no-store'});
        if(response.ok){const cache=await caches.open(CACHE);await cache.put('./index.html',response.clone());}
        return response;
      }catch(err){const cache=await caches.open(CACHE);return await cache.match('./index.html')||Response.error();}
    })());
  }else{
    event.respondWith((async()=>{
      const cached=await caches.match(request);
      if(cached) return cached;
      try {const response=await fetch(request); if(response.ok){const cache=await caches.open(CACHE);await cache.put(request,response.clone());} return response;}
      catch(err){return Response.error();}
    })());
  }
});
