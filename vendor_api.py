"""The vendor dashboard: see today's orders and move them along (owner: B).

New -> Cooking -> Ready -> Picked up. The allowed moves live in queue_rules.py.
"""

from flask import Blueprint, jsonify, render_template, request

from models import Order, Vendor, db
from payment_rules import COUNTER, TRANSFER, can_start_cooking
from push_api import notify_ready
from queue_rules import CANCELLED, COOKING, DONE, READY, WAITING, can_move, today

vendor_api = Blueprint("vendor_api", __name__)


@vendor_api.route("/vendor")
def vendor_page():
    return render_template("vendor.html")


@vendor_api.route("/api/vendor-list")
def vendor_list():
    """Every vendor, for the dashboard's drop-down."""
    rows = db.session.execute(db.select(Vendor).order_by(Vendor.hall, Vendor.name)).scalars().all()
    return jsonify([v.to_dict() for v in rows])


@vendor_api.route("/api/vendors/<slug>/orders")
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
    return jsonify(vendor=vendor.to_dict(), orders=[o.to_dict() for o in orders])


@vendor_api.route("/api/orders/<int:order_id>/status", methods=["POST"])
def set_status(order_id):
    """Move an order on. Send JSON: {"status": "cooking"}."""
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify(error="No such order"), 404
    data = request.get_json(silent=True)
    new = data.get("status") if isinstance(data, dict) else None
    if not can_move(order.status, new):
        return jsonify(error=f"An order that is {order.status} cannot become {new}"), 409
    if new == COOKING and not can_start_cooking(order.payment, order.paid):
        return jsonify(error=f"Ticket #{order.ticket} pays by transfer: confirm the money arrived first"), 409
    order.status = new
    if new == DONE and order.payment == COUNTER:
        order.paid = True  # the student paid at the counter when they picked it up
    db.session.commit()
    if new == READY:
        notify_ready(order)  # the student's phone buzzes, if they turned notifications on
    return jsonify(order.to_dict())


@vendor_api.route("/api/orders/<int:order_id>/paid", methods=["POST"])
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
