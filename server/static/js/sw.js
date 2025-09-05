// Service Worker pour les notifications push
self.addEventListener('push', function(event) {
    const options = {
        body: event.data.text(),
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        },
        actions: [
            {
                action: 'explore',
                title: 'Voir détails',
                icon: '/static/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fermer',
                icon: '/static/images/xmark.png'
            },
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Kin-doctor', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    if (event.action === 'explore') {
        // Ouvrir l'application sur la page appropriée
        clients.openWindow('/dashboard/');
    }
});

// Cache des ressources statiques
const CACHE_NAME = 'kin-doctor-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/images/logo.png',
    // Ajoutez d'autres ressources à mettre en cache
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});
