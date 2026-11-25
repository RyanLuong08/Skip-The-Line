"""The stats page (/stats): one day's orders at a glance, for the team and the presentation (owner: A).

Needs the vendor PIN, like the dashboard. The numbers come from stats.summarize().
"""

import re

from flask import Blueprint, jsonify, render_template, request

from models import Order, Vendor, db
from queue_rules import today
from staff_auth import staff_required
from stats import summarize

stats_api = Blueprint("stats_api", __name__)

DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


@stats_api.route("/stats")
@staff_required
def stats_page():
    return render_template("stats.html")


@stats_api.route("/api/stats")
@staff_required
def stats_data():
    """Stats for ?day=2026-11-25 (default: today)."""
    day = request.args.get("day") or today()
    if not DAY.fullmatch(day):
        return jsonify(error="day must look like 2026-11-25"), 400
    orders = db.session.execute(db.select(Order).where(Order.day == day)).scalars().all()
    vendors = {v.slug: {"name": v.name, "avg_prep_min": v.avg_prep_min}
               for v in db.session.execute(db.select(Vendor)).scalars()}
    rows = [{"vendor": o.vendor.slug, "status": o.status, "total": o.total, "payment": o.payment,
             "created_at": o.created_at, "cooking_at": o.cooking_at, "ready_at": o.ready_at}
            for o in orders]
    return jsonify(day=day, **summarize(rows, vendors))
