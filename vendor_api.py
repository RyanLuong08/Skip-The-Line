"""The vendor dashboard: see today's orders and move them along (owner: B).

New -> Cooking -> Ready -> Picked up. The allowed moves live in queue_rules.py.
"""

from flask import Blueprint, jsonify, render_template, request

from models import Order, Vendor, db
from queue_rules import COOKING, READY, WAITING, can_move, today

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
    order.status = new
    db.session.commit()
    return jsonify(order.to_dict())
