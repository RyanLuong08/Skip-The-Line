"""The vendor dashboard: see today's orders and move them along (owner: B).

New -> Cooking -> Ready -> Picked up (or No-show). The allowed moves live in queue_rules.py.
Vendors can also pause app orders for the day and mark dishes sold out for the day.
Everything here needs the vendor PIN (staff_auth.py).
"""

from flask import Blueprint, jsonify, render_template, request

from menu_import import HALLS
from models import MenuItem, Order, Vendor, db
from noshow_rules import NO_SHOW_AFTER_MIN, can_mark_no_show, minutes_until_no_show
from payment_rules import COUNTER, TRANSFER, can_start_cooking
from push_api import notify_ready
from queue_rules import CANCELLED, COOKING, DONE, NO_SHOW, READY, WAITING, can_move, now, today
from staff_auth import staff_required

vendor_api = Blueprint("vendor_api", __name__)


@vendor_api.route("/vendor")
@staff_required
def vendor_page():
    return render_template("vendor.html")


@vendor_api.route("/api/vendor-list")
@staff_required
def vendor_list():
    """Every vendor, for the dashboard's drop-down."""
    rows = db.session.execute(db.select(Vendor).order_by(Vendor.hall, Vendor.name)).scalars().all()
    halls = {h["id"]: h for h in HALLS}
    return jsonify([{**v.to_dict(), "hall_name": halls[v.hall]["name"], "hall_name_zh": halls[v.hall]["name_zh"]}
                    for v in rows])


@vendor_api.route("/api/vendors/<slug>/orders")
@staff_required
def vendor_orders(slug):
    """Today's orders that still need something from the vendor, by ticket number."""
    vendor = db.session.execute(db.select(Vendor).filter_by(slug=slug)).scalar_one_or_none()
    if vendor is None:
        return jsonify(error="No such vendor"), 404
    orders = db.session.execute(
        db.select(Order)
        .where(Order.vendor_id == vendor.id, Order.day == today(),
               Order.status.in_((WAITING, COOKING, READY)))
        .order_by(Order.ticket)
    ).scalars().all()
    moment = now()
    rows = []
    for o in orders:
        row = o.to_dict()
        if o.status == READY:
            row["no_show_in"] = minutes_until_no_show(o.ready_at, moment)
        rows.append(row)
    return jsonify(vendor=vendor.to_dict(), orders=rows)


@vendor_api.route("/api/orders/<int:order_id>/status", methods=["POST"])
@staff_required
def set_status(order_id):
    """Move an order on. Send JSON: {"status": "cooking"}."""
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify(error="No such order"), 404
    data = request.get_json(silent=True)
    new = data.get("status") if isinstance(data, dict) else None
    if not can_move(order.status, new):
        return jsonify(error=f"An order that is {order.status} cannot become {new}"), 409
    if new == NO_SHOW and not can_mark_no_show(order.ready_at, now()):
        return jsonify(error=f"Give the student {NO_SHOW_AFTER_MIN} minutes after Mark ready "
                             f"({minutes_until_no_show(order.ready_at, now())} min left)"), 409
    if new == COOKING and not can_start_cooking(order.payment, order.paid):
        return jsonify(error=f"Ticket #{order.ticket} pays by transfer: confirm the money arrived first"), 409
    order.status = new
    if new == COOKING:
        order.cooking_at = now()
    elif new == READY:
        order.ready_at = now()  # stats.py uses these two times to measure real cooking time
    if new == DONE and order.payment == COUNTER:
        order.paid = True  # the student paid at the counter when they picked it up
    db.session.commit()
    if new == READY:
        notify_ready(order)  # the student's phone buzzes, if they turned notifications on
    return jsonify(order.to_dict())


@vendor_api.route("/api/orders/<int:order_id>/paid", methods=["POST"])
@staff_required
def confirm_paid(order_id):
    """The vendor found the transfer in their bank app (matching the last 5 digits)."""
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify(error="No such order"), 404
    if order.payment != TRANSFER:
        return jsonify(error="This order is paid at the counter"), 409
    if order.status == CANCELLED:
        return jsonify(error="This order was cancelled"), 409
    order.paid = True
    db.session.commit()
    return jsonify(order.to_dict())


def _flag(data, key):
    """{"paused": true} -> True. Anything that isn't a real true/false -> None."""
    value = data.get(key) if isinstance(data, dict) else None
    return value if isinstance(value, bool) else None


@vendor_api.route("/api/vendors/<slug>/pause", methods=["POST"])
@staff_required
def pause_orders(slug):
    """Stop (or restart) app orders for the rest of today. Send JSON: {"paused": true}."""
    vendor = db.session.execute(db.select(Vendor).filter_by(slug=slug)).scalar_one_or_none()
    if vendor is None:
        return jsonify(error="No such vendor"), 404
    paused = _flag(request.get_json(silent=True), "paused")
    if paused is None:
        return jsonify(error='Send {"paused": true} or {"paused": false}'), 400
    vendor.paused_day = today() if paused else ""
    db.session.commit()
    return jsonify(vendor.to_dict())


@vendor_api.route("/api/items/<int:item_id>/sold-out", methods=["POST"])
@staff_required
def sold_out(item_id):
    """Mark a dish sold out for today (or back on). Send JSON: {"sold_out": true}."""
    item = db.session.get(MenuItem, item_id)
    if item is None:
        return jsonify(error="No such dish"), 404
    value = _flag(request.get_json(silent=True), "sold_out")
    if value is None:
        return jsonify(error='Send {"sold_out": true} or {"sold_out": false}'), 400
    item.sold_out_day = today() if value else ""
    db.session.commit()
    return jsonify(item.to_dict())
