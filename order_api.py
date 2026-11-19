"""Students place orders and follow their tickets (owner: A).

The browser only sends which dishes, how many and how the student wants to pay: Python
looks up the prices, checks the payment choice (payment_rules.py), gives out the ticket
number and works out how many orders are ahead.

There are no student accounts. The ids of a student's orders are kept in their
(signed) session cookie, so "My tickets" shows only their own orders.
"""

from flask import Blueprint, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from models import MenuItem, Order, OrderLine, Vendor, active_order_ids, db
from order_input import parse_items, parse_pickup
from payment_rules import bank_account, check_payment
from queue_rules import next_ticket, today

order_api = Blueprint("order_api", __name__)

SESSION_KEY = "my_orders"
MAX_REMEMBERED = 20  # a student's session remembers their last 20 orders


def orders_ahead(order):
    """How many orders at the same vendor are still being made and were placed before this one."""
    ids = active_order_ids(order.vendor_id, order.day)
    return ids.index(order.id) if order.id in ids else 0


def _create_order(vendor, items, pickup, payment, transfer_ref):
    """Save the order with the next ticket number. Returns the Order."""
    day = today()
    # Two students ordering at the same moment could both get the same number; the database
    # then refuses the second one (UniqueConstraint in models.Order), so we simply try again.
    for _attempt in range(3):
        last = db.session.execute(
            db.select(db.func.max(Order.ticket)).where(Order.vendor_id == vendor.id, Order.day == day)
        ).scalar()
        order = Order(vendor=vendor, day=day, ticket=next_ticket(last), pickup=pickup,
                      payment=payment, transfer_ref=transfer_ref)
        for item, qty in items:
            order.lines.append(OrderLine(menu_item_id=item.id, name=item.name, price=item.price, qty=qty))
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

    # Every dish must really belong to this vendor.
    dishes = {item.id: item for item in vendor.items}
    if any(item_id not in dishes for item_id in wanted):
        return jsonify(error="One of those dishes is not on this vendor's menu"), 400

    items = [(dishes[i], qty) for i, qty in wanted.items()]
    total = sum((item.price or 0) * qty for item, qty in items)
    unpriced = any(item.price is None for item, _qty in items)
    try:
        transfer_ref = check_payment(data.get("payment"), total, unpriced,
                                     bank_account(vendor.slug) is not None, data.get("transfer_ref"))
    except ValueError as err:
        return jsonify(error=str(err)), 400

    try:
        order = _create_order(vendor, items, pickup, data["payment"], transfer_ref)
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
