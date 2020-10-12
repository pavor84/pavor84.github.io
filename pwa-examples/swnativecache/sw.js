self.addEventListener('install', function(e) {
 e.waitUntil(
   caches.open('fox-store').then(function(cache) {
     return cache.addAll([
       '/pwa-examples/swnativecache/index.js',
       '/pwa-examples/swnativecache/style.css',
       '/pwa-examples/swnativecache/images/fox1.jpg',
       '/pwa-examples/swnativecache/images/fox2.jpg',
       '/pwa-examples/swnativecache/images/fox3.jpg',
       '/pwa-examples/swnativecache/images/fox4.jpg'
     ]);
   })
 );
});

self.addEventListener('fetch', function(e) {
  console.log(e.request.url);
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
