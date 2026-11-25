"""Students place orders and follow their tickets (owner: A).

The browser only sends which dishes, how many and how the student wants to pay: Python
looks up the prices, checks the payment choice (payment_rules.py), gives out the ticket
number and works out how many orders are ahead.

There are no student accounts. The ids of a student's orders are kept in their
(signed) session cookie, so "My tickets" shows only their own orders. The same cookie holds a
random browser id, used to count no-shows (noshow_rules.py).
"""

import secrets

from flask import Blueprint, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from models import MenuItem, Order, OrderLine, Vendor, active_order_ids, db
from noshow_rules import NO_SHOW_LIMIT, counter_blocked, oldest_counted_day
from opening_hours import next_opening, parse_hours, pickup_allowed
from order_input import parse_items, parse_pickup
from payment_rules import COUNTER, bank_account, check_payment
from queue_rules import CANCELLED, NO_SHOW, WAITING, next_ticket, now, today

order_api = Blueprint("order_api", __name__)

SESSION_KEY = "my_orders"
MAX_REMEMBERED = 20  # a student's session remembers their last 20 orders
DEVICE_KEY = "device"
RECENT_COUNT = 4     # how many past orders "Order again" offers


def device_id():
    """This browser's random id, made the first time it is needed."""
    if DEVICE_KEY not in session:
        session[DEVICE_KEY] = secrets.token_hex(16)
    session.permanent = True  # keep the cookie for weeks, not just until the browser closes
    return session[DEVICE_KEY]


def no_show_count(device):
    """How many of this browser's orders were never picked up, in the last NO_SHOW_DAYS days."""
    if not device:
        return 0
    return db.session.execute(
        db.select(db.func.count(Order.id))
        .where(Order.device == device, Order.status == NO_SHOW, Order.day >= oldest_counted_day(now()))
    ).scalar()


def orders_ahead(order):
    """How many orders at the same vendor are still being made and were placed before this one."""
    ids = active_order_ids(order.vendor_id, order.day)
    return ids.index(order.id) if order.id in ids else 0


def _create_order(vendor, items, pickup, payment, transfer_ref, push_sub_id=None, device=""):
    """Save the order with the next ticket number. Returns the Order."""
    day = today()
    # Two students ordering at the same moment could both get the same number; the database
    # then refuses the second one (UniqueConstraint in models.Order), so we simply try again.
    for _attempt in range(3):
        last = db.session.execute(
            db.select(db.func.max(Order.ticket)).where(Order.vendor_id == vendor.id, Order.day == day)
        ).scalar()
        order = Order(vendor=vendor, day=day, ticket=next_ticket(last), pickup=pickup,
                      payment=payment, transfer_ref=transfer_ref, push_sub_id=push_sub_id, device=device)
        for item, qty in items:
            order.lines.append(OrderLine(menu_item_id=item.id, name=item.name, name_zh=item.name_zh,
                                         price=item.price, qty=qty))
        order.total = sum((item.price or 0) * qty for item, qty in items)
        db.session.add(order)
        try:
            db.session.commit()
            return order
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError("Too many orders at once")


@order_api.route("/api/orders", methods=["POST"])
def place_order():
    """Place an order. Send JSON: {"vendor": "fengyun-love-curry",
    "items": [{"id": 12, "qty": 2}], "pickup": "ASAP" or "12:30",
    "payment": "transfer" or "counter", "transfer_ref": "12345" (only for transfer)}."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send the order as JSON"), 400

    vendor = db.session.execute(
        db.select(Vendor).filter_by(slug=str(data.get("vendor", "")))).scalar_one_or_none()
    if vendor is None:
        return jsonify(error="No such vendor"), 404

    try:
        wanted = parse_items(data.get("items"))
        pickup = parse_pickup(data.get("pickup"))
    except ValueError as err:
        return jsonify(error=str(err)), 400

    if vendor.paused_day == today():
        return jsonify(error=f"{vendor.name} has paused app orders for now. Please order at the counter."), 409

    windows = parse_hours(vendor.hours)
    if not pickup_allowed(windows, pickup):
        opens = next_opening(windows)
        when = f" It opens again at {opens}." if opens else " It is closed for the rest of today."
        return jsonify(error=f"{vendor.name} is closed at that time.{when}"), 400

    # Every dish must really belong to this vendor.
    dishes = {item.id: item for item in vendor.items}
    if any(item_id not in dishes for item_id in wanted):
        return jsonify(error="One of those dishes is not on this vendor's menu"), 400

    sold_out = [dishes[i].name for i in wanted if dishes[i].sold_out]
    if sold_out:
        return jsonify(error=f"Sorry, sold out today: {', '.join(sold_out)}. Remove it and try again."), 400

    items = [(dishes[i], qty) for i, qty in wanted.items()]
    device = device_id()
    if data.get("payment") == COUNTER and counter_blocked(no_show_count(device)):
        return jsonify(error=f"You didn't pick up {NO_SHOW_LIMIT} orders, so pay at pickup is off for you. "
                             "Please pay by bank transfer."), 403
    total = sum((item.price or 0) * qty for item, qty in items)
    unpriced = any(item.price is None for item, _qty in items)
    try:
        transfer_ref = check_payment(data.get("payment"), total, unpriced,
                                     bank_account(vendor.slug) is not None, data.get("transfer_ref"))
    except ValueError as err:
        return jsonify(error=str(err)), 400

    try:
        order = _create_order(vendor, items, pickup, data["payment"], transfer_ref,
                              push_sub_id=session.get("push_sub"),  # push_api.SESSION_KEY
                              device=device)
    except RuntimeError:
        return jsonify(error="The vendor is very busy. Please try again."), 503

    mine = session.get(SESSION_KEY, [])
    session[SESSION_KEY] = (mine + [order.id])[-MAX_REMEMBERED:]
    return jsonify(order.to_dict(ahead=orders_ahead(order))), 201


@order_api.route("/api/my-orders")
def my_orders():
    """Today's orders placed from this browser, newest first, with how many are ahead."""
    ids = session.get(SESSION_KEY, [])
    if not ids:
        return jsonify([])
    orders = db.session.execute(
        db.select(Order).where(Order.id.in_(ids), Order.day == today()).order_by(Order.id.desc())
    ).scalars().all()
    return jsonify([o.to_dict(ahead=orders_ahead(o)) for o in orders])


@order_api.route("/api/my-orders/<int:order_id>/cancel", methods=["POST"])
def cancel_my_order(order_id):
    """A student cancels their own order. Only before the vendor starts cooking it, and not
    once the vendor has confirmed a transfer (then the money has to be refunded at the counter)."""
    if order_id not in session.get(SESSION_KEY, []):
        return jsonify(error="That's not one of your orders"), 404
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify(error="No such order"), 404
    if order.status != WAITING:
        return jsonify(error="The vendor has already started this order, so it can't be cancelled"), 409
    if order.paid:
        return jsonify(error="The vendor already received your transfer. Ask at the counter to cancel"), 409
    order.status = CANCELLED
    db.session.commit()
    return jsonify(order.to_dict())


@order_api.route("/api/my-orders/recent")
def recent_orders():
    """This browser's last few orders (any day, not cancelled), newest first, for "Order again".
    The same dishes from the same vendor show only once."""
    ids = session.get(SESSION_KEY, [])
    if not ids:
        return jsonify([])
    orders = db.session.execute(
        db.select(Order).where(Order.id.in_(ids), Order.status != CANCELLED).order_by(Order.id.desc())
    ).scalars().all()
    recent, seen = [], set()
    for o in orders:
        key = (o.vendor_id, tuple(sorted((line.menu_item_id or 0, line.qty) for line in o.lines)))
        if key not in seen:
            seen.add(key)
            recent.append(o.to_dict())
        if len(recent) == RECENT_COUNT:
            break
    return jsonify(recent)


@order_api.route("/api/me")
def me():
    """This browser's no-show count, so the page can warn before pay at pickup is switched off."""
    count = no_show_count(session.get(DEVICE_KEY))
    return jsonify(no_shows=count, no_show_limit=NO_SHOW_LIMIT, counter_blocked=counter_blocked(count))
