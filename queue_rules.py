"""Queue rules: tickets, wait times, pickup times and order status (owner: A).

Plain Python with no Flask and no database, so it is easy to test.

Every vendor gives out ticket numbers 1, 2, 3, ... starting again each day.
An order moves through: waiting -> cooking -> ready -> done (picked up).
A waiting order can also be cancelled.
"""

from datetime import datetime, timedelta, timezone

# Taiwan has no daylight saving time, so a fixed +8 hours is always right
# (and it works on Windows, which has no built-in time zone database).
TAIPEI = timezone(timedelta(hours=8))

WAITING = "waiting"
COOKING = "cooking"
READY = "ready"
DONE = "done"
CANCELLED = "cancelled"
NO_SHOW = "no_show"                  # ready, but the student never came (see noshow_rules.py)

ACTIVE = (WAITING, COOKING)          # still being made: these count towards the wait
STATUSES = (WAITING, COOKING, READY, DONE, CANCELLED, NO_SHOW)

# Which status an order may move to from each status.
ALLOWED_MOVES = {
    WAITING: {COOKING, CANCELLED},
    COOKING: {READY},
    READY: {DONE, NO_SHOW},
    DONE: set(),
    CANCELLED: set(),
    NO_SHOW: set(),
}

ASAP = "ASAP"
SLOT_STEP_MIN = 10      # pickup times are offered every 10 minutes
SLOT_COUNT = 9          # ... for the next 90 minutes
LATEST_PICKUP_MIN = 120 # nobody can order for later than 2 hours from now

# Lunch and dinner rushes (24-hour clock). Change these once the survey shows the real ones.
PEAK_HOURS = (("11:50", "12:40"), ("17:20", "18:30"))


def now():
    """The current time in Taiwan, without time zone info (that is how SQLite stores it)."""
    return datetime.now(TAIPEI).replace(tzinfo=None)


def today(moment=None):
    """Today's date as text, e.g. "2026-11-19". Tickets start again from 1 each day."""
    return (moment or now()).strftime("%Y-%m-%d")


def next_ticket(last_ticket):
    """The ticket number after the vendor's last one today (None if there is none yet)."""
    return (last_ticket or 0) + 1


def can_move(current, new):
    """True if an order may change from status `current` to status `new`."""
    return new in ALLOWED_MOVES.get(current, set())


def estimate_wait_min(orders_in_queue, avg_prep_min):
    """Rough minutes until a new order would be ready: orders ahead x minutes per order."""
    return orders_in_queue * avg_prep_min


def wait_level(minutes):
    """"low", "mid" or "high", for colouring the wait time on the page."""
    if minutes <= 5:
        return "low"
    if minutes <= 15:
        return "mid"
    return "high"


def _minute_of_day(hhmm):
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def is_peak(moment=None):
    """True during the lunch or dinner rush."""
    moment = moment or now()
    minute = moment.hour * 60 + moment.minute
    return any(_minute_of_day(start) <= minute < _minute_of_day(end) for start, end in PEAK_HOURS)


def pickup_slots(moment=None):
    """["ASAP", "12:10", "12:20", ...]: the pickup times a student can choose right now.

    The first time slot is at least SLOT_STEP_MIN minutes away, so the vendor has time to cook.
    """
    moment = moment or now()
    minute = moment.hour * 60 + moment.minute
    first = -(-(minute + SLOT_STEP_MIN) // SLOT_STEP_MIN) * SLOT_STEP_MIN  # round up
    slots = [ASAP]
    for i in range(SLOT_COUNT):
        slot = first + i * SLOT_STEP_MIN
        if slot >= 24 * 60:
            break  # no pickups after midnight
        slots.append(f"{slot // 60:02d}:{slot % 60:02d}")
    return slots
