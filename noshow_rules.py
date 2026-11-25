"""No-show rule: students who order and never pick up (owner: A).

Plain Python with no Flask and no database, so it is easy to test.

When food has been ready for NO_SHOW_AFTER_MIN minutes and nobody came, the vendor can press
"No-show". After NO_SHOW_LIMIT no-shows in the last NO_SHOW_DAYS days, that browser can't use
"Pay at pickup" any more: it has to pay by bank transfer first, so the vendor is never left with
unpaid food again.

There are no student accounts, so a "student" here is one browser (a random id kept in its
session cookie). Someone who clears their cookies starts again from zero. Stopping that would
need a real login, e.g. with the student ID.

The team still has to agree on the number: change NO_SHOW_LIMIT if the slides say 2.
"""

from datetime import timedelta

NO_SHOW_LIMIT = 3          # no-shows before "Pay at pickup" is switched off for that browser
NO_SHOW_AFTER_MIN = 15     # minutes an order must have been ready before it can be marked no-show
NO_SHOW_DAYS = 30          # only no-shows from the last 30 days count


def can_mark_no_show(ready_at, moment):
    """True once the food has waited NO_SHOW_AFTER_MIN minutes (so nobody is marked by mistake)."""
    return ready_at is not None and moment - ready_at >= timedelta(minutes=NO_SHOW_AFTER_MIN)


def minutes_until_no_show(ready_at, moment):
    """Whole minutes left before "No-show" is allowed (0 if it already is)."""
    if ready_at is None:
        return NO_SHOW_AFTER_MIN
    left = timedelta(minutes=NO_SHOW_AFTER_MIN) - (moment - ready_at)
    return max(0, -(-int(left.total_seconds()) // 60))


def counter_blocked(no_shows):
    """True if this browser has too many no-shows to pay at pickup."""
    return no_shows >= NO_SHOW_LIMIT


def oldest_counted_day(moment):
    """Orders on or after this day ("YYYY-MM-DD") count towards the limit."""
    return (moment - timedelta(days=NO_SHOW_DAYS - 1)).strftime("%Y-%m-%d")
