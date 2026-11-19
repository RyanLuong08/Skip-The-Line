"""Push notification rules (owner: B).

Plain Python with no Flask and no database, so it is easy to test.
push_api.py does the sending; this file checks what the browser sends and words the message.
"""

from urllib.parse import urlsplit

# The server will send messages to whatever address the browser gives it, so only accept
# the real push services of Chrome/Android, Firefox, Safari/iPhone and Edge.
PUSH_HOSTS = ("fcm.googleapis.com", "push.services.mozilla.com", "push.apple.com", "notify.windows.com")

MAX_ENDPOINT = 500
MAX_KEY = 200


def _allowed_host(host):
    return any(host == allowed or host.endswith("." + allowed) for allowed in PUSH_HOSTS)


def parse_subscription(data):
    """Check a browser's PushSubscription (as JSON) and return (endpoint, p256dh, auth)."""
    if not isinstance(data, dict) or not isinstance(data.get("keys"), dict):
        raise ValueError("Send the subscription from pushManager.subscribe()")
    endpoint, keys = data.get("endpoint"), data["keys"]
    p256dh, auth = keys.get("p256dh"), keys.get("auth")
    if not isinstance(endpoint, str) or len(endpoint) > MAX_ENDPOINT:
        raise ValueError("Bad push address")
    parts = urlsplit(endpoint)
    if parts.scheme != "https" or not _allowed_host((parts.hostname or "").lower()):
        raise ValueError("That is not a known push service")
    for key in (p256dh, auth):
        if not isinstance(key, str) or not key or len(key) > MAX_KEY:
            raise ValueError("Bad push keys")
    return endpoint, p256dh, auth


def ready_message(ticket, vendor_name):
    """What the phone shows when an order is ready."""
    return {"title": f"#{ticket} is ready!",
            "body": f"{vendor_name}: show this number at the counter.",
            "tag": f"ticket-{vendor_name}-{ticket}"}
