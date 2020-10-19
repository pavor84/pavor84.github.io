self.addEventListener('install', function(e) {
 e.waitUntil(
   caches.open('fox-store').then(function(cache) {
     return cache.addAll([
       '/pwa-examples/nativecachesw/index.js',
       '/pwa-examples/nativecachesw/style.css',
       '/pwa-examples/nativecachesw/images/fox1.jpg',
       '/pwa-examples/nativecachesw/images/fox2.jpg',
       '/pwa-examples/nativecachesw/images/fox3.jpg',
       '/pwa-examples/nativecachesw/images/fox4.jpg'
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
