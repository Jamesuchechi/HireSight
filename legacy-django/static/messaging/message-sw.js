'use strict';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

function showMessageNotification({ title, body, url }) {
    if (!title) {
        return;
    }
    const options = {
        body: body || 'You have a new message',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-72x72.png',
        data: {
            url: url || '/',
        },
    };
    return self.registration.showNotification(title, options);
}

self.addEventListener('message', (event) => {
    const payload = event.data;
    if (!payload || payload.type !== 'new_message') {
        return;
    }
    event.waitUntil(showMessageNotification(payload));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = event.notification.data?.url || '/';
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            const matchingClient = clientList.find((client) => client.url === targetUrl);
            if (matchingClient) {
                return matchingClient.focus();
            }
            return self.clients.openWindow(targetUrl);
        })
    );
});
