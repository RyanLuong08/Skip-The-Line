"""Check what a student sends when they place an order (owner: A).

Plain Python with no Flask and no database, so it is easy to test.
Never trust what the browser sends: it could be anything, so every value is checked here
and a ValueError explains what is wrong.
"""

from queue_rules import ASAP, LATEST_PICKUP_MIN, now

MAX_LINES = 20        # different dishes in one order
MAX_QTY = 10          # of one dish


def parse_items(raw_items):
    """Turn [{"id": 3, "qty": 2}, ...] into {3: 2, ...}. The same dish twice is added up."""
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Add at least one dish to your order.")
    if len(raw_items) > MAX_LINES:
        raise ValueError(f"An order can have at most {MAX_LINES} different dishes.")

    items = {}
    for line in raw_items:
        if not isinstance(line, dict):
            raise ValueError("Each dish needs an id and a qty.")
        item_id, qty = line.get("id"), line.get("qty", 1)
        # bool is a kind of int in Python, so rule it out on purpose
        if not isinstance(item_id, int) or isinstance(item_id, bool):
            raise ValueError("Each dish id must be a whole number.")
        if not isinstance(qty, int) or isinstance(qty, bool) or not 1 <= qty <= MAX_QTY:
            raise ValueError(f"Quantity must be a whole number from 1 to {MAX_QTY}.")
        items[item_id] = items.get(item_id, 0) + qty
        if items[item_id] > MAX_QTY:
            raise ValueError(f"You can order at most {MAX_QTY} of one dish.")
    return items


def parse_pickup(value, moment=None):
    """Return "ASAP" or a time like "12:30" that is not in the past and at most 2 hours away."""
    if value in (None, "", ASAP):
        return ASAP
    if not isinstance(value, str):
        raise ValueError('Pickup time must be "ASAP" or a time like 12:30.')
    try:
        hours, minutes = (int(part) for part in value.split(":"))
    except ValueError:
        raise ValueError('Pickup time must be "ASAP" or a time like 12:30.') from None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError('Pickup time must be "ASAP" or a time like 12:30.')

    moment = moment or now()
    current = moment.hour * 60 + moment.minute
    chosen = hours * 60 + minutes
    if chosen < current - 5:  # a few minutes' grace: the page may have been open a while
        raise ValueError("That pickup time has already passed. Pick a later one.")
    if chosen > current + LATEST_PICKUP_MIN:
        raise ValueError("You can order at most 2 hours ahead.")
    return f"{hours:02d}:{minutes:02d}"
