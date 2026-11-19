"""Web Push: the phone gets a notification (and vibrates) when an order is ready,
even if the page is closed or the screen is off (owner: B).

How it works:
1. The student taps "Notify me" on the page. The browser asks for permission and gives us a
   "subscription" (an address at Google/Apple/Mozilla's push service plus two keys).
2. We save it (models.PushSubscription) and remember its id in the student's session, so every
   order they place from that browser knows where to send the message.
3. When the vendor presses "Mark ready", vendor_api.py calls notify_ready(order). pywebpush
   encrypts the message and posts it to the push service, which wakes the phone up.
   static/sw.js (the service worker) then shows the notification.

Needs: `pip install -r requirements.txt` (pywebpush) and an https:// address (ngrok) or
localhost: browsers only allow push on secure pages. Without pywebpush the app still runs,
only the "Notify me" button is hidden.

The server's own key pair (VAPID) is made once and kept in instance/vapid_private.pem
(git ignores instance/), so subscriptions keep working after a restart.
"""

import base64
import json
import os
import threading

from flask import Blueprint, current_app, jsonify, request, session

from models import Order, PushSubscription, db
from push_rules import parse_subscription, ready_message
from queue_rules import ACTIVE, READY, today

push_api = Blueprint("push_api", __name__)

KEY_FILE = "vapid_private.pem"
SESSION_KEY = "push_sub"
# Push services want a way to contact whoever sends the messages.
CONTACT = os.environ.get("VAPID_CONTACT", "https://github.com/RyanLuong08/Skip-The-Line")


def setup_push(app, enabled=True):
    """Find or make the VAPID key. Sets app.config["VAPID_PUBLIC_KEY"] (None = push is off)."""
    app.config["VAPID_KEY_FILE"] = None
    app.config["VAPID_PUBLIC_KEY"] = None
    if not enabled:
        return
    try:
        import pywebpush  # noqa: F401  (only checking that it is installed)
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
    except ImportError:
        app.logger.warning("pywebpush is not installed, so push notifications are off")
        return

    path = os.path.join(app.instance_path, KEY_FILE)
    if os.path.exists(path):
        with open(path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    else:
        private_key = ec.generate_private_key(ec.SECP256R1())
        os.makedirs(app.instance_path, exist_ok=True)
        with open(path, "wb") as f:
            f.write(private_key.private_bytes(serialization.Encoding.PEM,
                                              serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
    public = private_key.public_key().public_bytes(serialization.Encoding.X962,
                                                   serialization.PublicFormat.UncompressedPoint)
    app.config["VAPID_KEY_FILE"] = path
    app.config["VAPID_PUBLIC_KEY"] = base64.urlsafe_b64encode(public).decode().rstrip("=")


@push_api.route("/api/push/key")
def public_key():
    """The page needs this key to subscribe. null means push is switched off on this server."""
    return jsonify(key=current_app.config.get("VAPID_PUBLIC_KEY"))


@push_api.route("/api/push/subscribe", methods=["POST"])
def subscribe():
    """Save this browser's subscription, and use it for this browser's orders that aren't ready yet."""
    if not current_app.config.get("VAPID_PUBLIC_KEY"):
        return jsonify(error="Push notifications are off on this server"), 503
    try:
        endpoint, p256dh, auth = parse_subscription(request.get_json(silent=True))
    except ValueError as err:
        return jsonify(error=str(err)), 400

    sub = db.session.execute(db.select(PushSubscription).filter_by(endpoint=endpoint)).scalar_one_or_none()
    if sub is None:
        sub = PushSubscription(endpoint=endpoint)
        db.session.add(sub)
    sub.p256dh, sub.auth = p256dh, auth
    db.session.flush()  # gives sub its id

    session[SESSION_KEY] = sub.id
    ids = session.get("my_orders", [])  # order_api.SESSION_KEY
    if ids:
        db.session.execute(db.update(Order)
                           .where(Order.id.in_(ids), Order.day == today(), Order.status.in_(ACTIVE))
                           .values(push_sub_id=sub.id))
    db.session.commit()
    return jsonify(ok=True)


def notify_ready(order):
    """Tell the student's phone that this order is ready. Never slows down the vendor's page:
    the message is sent in the background, and any failure is only logged."""
    app = current_app._get_current_object()
    key_file = app.config.get("VAPID_KEY_FILE")
    if order.status != READY or not order.push_sub_id or not key_file:
        return
    sub = db.session.get(PushSubscription, order.push_sub_id)
    if sub is None:
        return
    message = json.dumps(ready_message(order.ticket, order.vendor.name))
    threading.Thread(target=_send, args=(app, key_file, sub.id, sub.info(), message), daemon=True).start()


def _send(app, key_file, sub_id, info, message):
    from pywebpush import WebPushException, webpush
    try:
        webpush(subscription_info=info, data=message, vapid_private_key=key_file,
                vapid_claims={"sub": CONTACT}, ttl=15 * 60, timeout=10)
    except WebPushException as err:
        status = getattr(err.response, "status_code", None)
        if status in (404, 410):  # the student turned notifications off: forget this phone
            with app.app_context():
                db.session.execute(db.delete(PushSubscription).where(PushSubscription.id == sub_id))
                db.session.commit()
        else:
            app.logger.warning("Push failed: %s", err)
    except Exception as err:  # no internet, push service down, ...
        app.logger.warning("Push failed: %s", err)
