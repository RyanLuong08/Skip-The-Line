"""Dining halls, vendors and menus, with live wait times (owner: B).

Like every *_api.py file, this lives in its own Blueprint. app.py only needs:

    from menu_api import menu_api
    app.register_blueprint(menu_api)
"""

from flask import Blueprint, jsonify, request

from menu_import import HALLS
from models import Vendor, db, queue_lengths
from payment_rules import COUNTER_LIMIT, bank_account
from queue_rules import estimate_wait_min, is_peak, pickup_slots, today, wait_level

menu_api = Blueprint("menu_api", __name__)


def vendor_summary(vendor, queue):
    """A vendor plus how busy it is right now."""
    wait = estimate_wait_min(queue, vendor.avg_prep_min)
    return {**vendor.to_dict(), "queue": queue, "wait_min": wait, "wait_level": wait_level(wait),
            "dish_count": len(vendor.items), "bank": bank_account(vendor.slug)}


@menu_api.route("/api/halls")
def halls():
    """The three dining halls and how many vendors each has."""
    counts = dict(db.session.execute(
        db.select(Vendor.hall, db.func.count()).group_by(Vendor.hall)).all())
    return jsonify([{"id": h["id"], "name": h["name"], "name_zh": h["name_zh"],
                     "vendor_count": counts.get(h["id"], 0)} for h in HALLS])


@menu_api.route("/api/vendors")
def vendors():
    """Vendors in one hall (?hall=fengyun), with their queue and estimated wait."""
    hall = request.args.get("hall", "fengyun")
    if hall not in {h["id"] for h in HALLS}:
        return jsonify(error="Unknown dining hall"), 404
    rows = db.session.execute(
        db.select(Vendor).where(Vendor.hall == hall).order_by(Vendor.name)).scalars().all()
    queues = queue_lengths(today())
    return jsonify([vendor_summary(v, queues.get(v.id, 0)) for v in rows])


@menu_api.route("/api/vendors/<slug>/menu")
def menu(slug):
    """One vendor's dishes."""
    vendor = db.session.execute(db.select(Vendor).filter_by(slug=slug)).scalar_one_or_none()
    if vendor is None:
        return jsonify(error="No such vendor"), 404
    queue = queue_lengths(today()).get(vendor.id, 0)
    return jsonify(vendor=vendor_summary(vendor, queue), items=[i.to_dict() for i in vendor.items])


@menu_api.route("/api/now")
def right_now():
    """Is it peak hour, which pickup times can a student choose, and the pay-at-pickup limit?"""
    return jsonify(peak=is_peak(), pickup_slots=pickup_slots(), counter_limit=COUNTER_LIMIT)
