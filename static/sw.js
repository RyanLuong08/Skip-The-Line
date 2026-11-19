// Service worker (served at /sw.js by app.py): shows the "your food is ready" notification
// that push_api.py sends, even when the Skip the Line page is closed or the screen is off.
// No sound is added here: the phone only vibrates (plus whatever its own notification settings do).

self.addEventListener("push", event => {
  let data = {};
  try { data = event.data.json(); } catch { /* not JSON: show the default text */ }
  event.waitUntil(self.registration.showNotification(data.title || "Your food is ready!", {
    body: data.body || "Show your ticket number at the counter.",
    tag: data.tag,                    // one notification per ticket, not a pile of them
    renotify: Boolean(data.tag),      // ... but buzz again if it is sent again
    vibrate: [300, 120, 300, 120, 300],
    requireInteraction: true,         // stays on screen until the student taps it
    data: { url: "/" },
  }));
});

// Tapping the notification opens (or brings back) the Skip the Line page.
self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil((async () => {
    const pages = await clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const page of pages) {
      if ("focus" in page) return page.focus();
    }
    return clients.openWindow(event.notification.data?.url || "/");
  })());
});
