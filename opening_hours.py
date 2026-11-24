"""Opening hours: is a vendor open, and which pickup times can a student choose (owner: B).

Plain Python with no Flask and no database, so it is easy to test.

A vendor's hours are written as text, e.g. "10:30-14:00, 16:30-19:30" (lunch and dinner).
They come from the opening_hours column of the menu CSV, or from OPENING_HOURS in
menu_import.py. Empty text means the hours haven't been collected yet: the vendor is then
treated as open all day, like before.
"""

from queue_rules import ASAP, now, pickup_slots


def _minutes(hhmm):
    hours, minutes = (int(part) for part in hhmm.strip().split(":"))
    if not (0 <= hours <= 24 and 0 <= minutes <= 59) or (hours == 24 and minutes):
        raise ValueError
    return hours * 60 + minutes


def parse_hours(text):
    """"10:30-14:00, 16:30-19:30" -> [(630, 840), (990, 1170)] (minutes after midnight).

    "" -> [] (hours unknown). Raises ValueError for anything else it can't read.
    """
    text = (text or "").strip()
    if not text:
        return []
    windows = []
    for part in text.replace("，", ",").replace(";", ",").split(","):
        try:
            start, end = (_minutes(t) for t in part.split("-"))
        except ValueError:
            raise ValueError(f'Opening hours must look like "10:30-14:00, 16:30-19:30", not "{text}"') from None
        if end <= start:
            raise ValueError(f'In "{part.strip()}" the closing time must be after the opening time')
        windows.append((start, end))
    return sorted(windows)


def _minute_of(moment):
    return moment.hour * 60 + moment.minute


def open_at(windows, minute):
    """True if the vendor is open at this minute of the day. Unknown hours count as open."""
    return not windows or any(start <= minute < end for start, end in windows)


def is_open(windows, moment=None):
    return open_at(windows, _minute_of(moment or now()))


def next_opening(windows, moment=None):
    """When a closed vendor opens again today, e.g. "16:30", or None if not again today."""
    minute = _minute_of(moment or now())
    later = [start for start, _end in windows if start > minute]
    return f"{later[0] // 60:02d}:{later[0] % 60:02d}" if later else None


def pickup_allowed(windows, pickup, moment=None):
    """ASAP needs the vendor to be open now; "12:30" needs it to be open at 12:30."""
    if pickup == ASAP:
        return is_open(windows, moment)
    return open_at(windows, _minutes(pickup))


def vendor_pickup_slots(windows, moment=None):
    """The pickup times a student can choose at this vendor right now (may be empty)."""
    moment = moment or now()
    return [slot for slot in pickup_slots(moment) if pickup_allowed(windows, slot, moment)]
