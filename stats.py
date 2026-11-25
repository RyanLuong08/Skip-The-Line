"""Numbers for the presentation: how busy each hour was, and how long food really took (owner: A).

Plain Python with no Flask and no database, so it is easy to test. stats_api.py turns the
day's orders into plain dicts and calls summarize().

Each order dict has: vendor (slug), status, total, payment, created_at, cooking_at, ready_at
(the last three are datetimes; cooking_at and ready_at are None until the vendor presses the button).
"""

from statistics import median

from queue_rules import CANCELLED, NO_SHOW

MIN_SAMPLES = 3  # don't suggest a new avg_prep_min from fewer cooked orders than this


def _minutes(start, end):
    return (end - start).total_seconds() / 60


def _average(values):
    return round(sum(values) / len(values), 1) if values else None


def summarize(orders, vendors):
    """orders: list of order dicts (see above). vendors: {slug: {"name", "avg_prep_min"}}.

    Returns a dict with:
      totals:  orders, cancelled, no_shows, revenue (NT$), transfer (number paid by transfer), avg_wait_min
      by_hour: [{"hour": 11, "orders": 7}, ...] from the first to the last busy hour, gaps as 0
      vendors: one row per vendor that had orders, busiest first, with avg_wait_min
               (ordered -> ready), avg_cook_min (cooking -> ready), set_prep_min (what the wait
               estimate uses now) and measured_prep_min (median cook time, once there are enough)
    """
    kept = [o for o in orders if o["status"] != CANCELLED]
    waits = [_minutes(o["created_at"], o["ready_at"]) for o in kept if o.get("ready_at")]

    totals = {
        "orders": len(kept),
        "cancelled": len(orders) - len(kept),
        "no_shows": sum(1 for o in kept if o["status"] == NO_SHOW),
        "revenue": sum(o["total"] for o in kept),
        "transfer": sum(1 for o in kept if o["payment"] == "transfer"),
        "avg_wait_min": _average(waits),
    }

    counts = {}
    for o in kept:
        counts[o["created_at"].hour] = counts.get(o["created_at"].hour, 0) + 1
    by_hour = ([{"hour": h, "orders": counts.get(h, 0)} for h in range(min(counts), max(counts) + 1)]
               if counts else [])

    rows = []
    for slug in {o["vendor"] for o in orders}:
        mine = [o for o in orders if o["vendor"] == slug]
        done = [o for o in mine if o["status"] != CANCELLED]
        cooked = [_minutes(o["cooking_at"], o["ready_at"]) for o in done if o.get("cooking_at") and o.get("ready_at")]
        info = vendors.get(slug, {"name": slug, "avg_prep_min": None})
        rows.append({
            "slug": slug,
            "name": info["name"],
            "orders": len(done),
            "cancelled": len(mine) - len(done),
            "no_shows": sum(1 for o in done if o["status"] == NO_SHOW),
            "revenue": sum(o["total"] for o in done),
            "avg_wait_min": _average([_minutes(o["created_at"], o["ready_at"]) for o in done if o.get("ready_at")]),
            "avg_cook_min": _average(cooked),
            "set_prep_min": info["avg_prep_min"],
            "measured_prep_min": max(1, round(median(cooked))) if len(cooked) >= MIN_SAMPLES else None,
        })
    rows.sort(key=lambda r: (-r["orders"], r["name"]))
    return {"totals": totals, "by_hour": by_hour, "vendors": rows}
