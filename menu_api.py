"""Dining halls, vendors and menus, with live wait times (owner: B).

Like every *_api.py file, this lives in its own Blueprint. app.py only needs:

    from menu_api import menu_api
    app.register_blueprint(menu_api)
"""

from flask import Blueprint, jsonify, request

from menu_import import HALLS
from models import MenuItem, Vendor, db, queue_lengths
from payment_rules import COUNTER_LIMIT, bank_account
from opening_hours import is_open, next_opening, parse_hours, vendor_pickup_slots
from queue_rules import estimate_wait_min, is_peak, pickup_slots, today, wait_level

menu_api = Blueprint("menu_api", __name__)


def vendor_summary(vendor, queue):
    """A vendor plus how busy it is right now and whether it is open.

    queue and wait_min only count orders placed in the app, not the line at the counter.
    """
    wait = estimate_wait_min(queue, vendor.avg_prep_min)
    windows = parse_hours(vendor.hours)
    return {**vendor.to_dict(), "queue": queue, "wait_min": wait, "wait_level": wait_level(wait),
            "dish_count": len(vendor.items), "bank": bank_account(vendor.slug),
            "open": is_open(windows), "opens_at": next_opening(windows),
            "pickup_slots": vendor_pickup_slots(windows)}


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
    """Is it peak hour, which pickup times can a student choose, and the pay-at-pickup limit?

    With ?vendor=<slug> the pickup times are only those when that vendor is open.
    """
    slots = pickup_slots()
    slug = request.args.get("vendor")
    if slug:
        vendor = db.session.execute(db.select(Vendor).filter_by(slug=slug)).scalar_one_or_none()
        if vendor is None:
            return jsonify(error="No such vendor"), 404
        slots = vendor_pickup_slots(parse_hours(vendor.hours))
    return jsonify(peak=is_peak(), pickup_slots=slots, counter_limit=COUNTER_LIMIT)


SEARCH_LIMIT = 40


def dish_matches(item, vendor, words):
    """True if every word appears in the dish or vendor name (English or Chinese) or its category."""
    text = " ".join((item.name, item.name_zh, vendor.name, vendor.name_zh, item.category)).lower()
    return all(word in text for word in words)


@menu_api.route("/api/search")
def search():
    """Dishes from every vendor in every hall. ?q=beef noodle  &veg=1  &max_price=100
    Sold-out dishes are left out. Cheapest first; open vendors before closed ones."""
    words = request.args.get("q", "").lower().split()
    veg = request.args.get("veg") == "1"
    try:
        max_price = int(request.args["max_price"]) if request.args.get("max_price") else None
    except ValueError:
        return jsonify(error="max_price must be a whole number"), 400
    if not words and not veg and max_price is None:
        return jsonify([])

    rows = db.session.execute(db.select(MenuItem, Vendor).join(Vendor)).all()
    queues = queue_lengths(today())
    halls = {h["id"]: h for h in HALLS}
    found = []
    summaries = {}
    for item, vendor in rows:
        if item.sold_out or (veg and not item.vegetarian):
            continue
        if max_price is not None and (item.price is None or item.price > max_price):
            continue
        if words and not dish_matches(item, vendor, words):
            continue
        if vendor.id not in summaries:
            summaries[vendor.id] = vendor_summary(vendor, queues.get(vendor.id, 0))
        v = summaries[vendor.id]
        found.append({**item.to_dict(), "vendor": {
            "slug": v["slug"], "name": v["name"], "name_zh": v["name_zh"], "open": v["open"],
            "paused": v["paused"], "wait_min": v["wait_min"],
            "hall": halls[vendor.hall]["name"], "hall_zh": halls[vendor.hall]["name_zh"]}})
    found.sort(key=lambda d: (not (d["vendor"]["open"] and not d["vendor"]["paused"]),
                              d["price"] is None, d["price"] or 0, d["name"]))
    return jsonify(found[:SEARCH_LIMIT])
