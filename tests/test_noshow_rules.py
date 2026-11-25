import unittest
from datetime import datetime, timedelta

from noshow_rules import (NO_SHOW_AFTER_MIN, NO_SHOW_DAYS, NO_SHOW_LIMIT, can_mark_no_show,
                          counter_blocked, minutes_until_no_show, oldest_counted_day)

READY = datetime(2026, 11, 25, 12, 0)


class TestNoShowRules(unittest.TestCase):
    def test_must_wait_after_ready(self):
        self.assertFalse(can_mark_no_show(READY, READY + timedelta(minutes=NO_SHOW_AFTER_MIN - 1)))
        self.assertTrue(can_mark_no_show(READY, READY + timedelta(minutes=NO_SHOW_AFTER_MIN)))
        self.assertFalse(can_mark_no_show(None, READY))

    def test_minutes_left(self):
        self.assertEqual(minutes_until_no_show(READY, READY), NO_SHOW_AFTER_MIN)
        self.assertEqual(minutes_until_no_show(READY, READY + timedelta(minutes=14, seconds=10)), 1)
        self.assertEqual(minutes_until_no_show(READY, READY + timedelta(hours=1)), 0)
        self.assertEqual(minutes_until_no_show(None, READY), NO_SHOW_AFTER_MIN)

    def test_limit(self):
        self.assertFalse(counter_blocked(NO_SHOW_LIMIT - 1))
        self.assertTrue(counter_blocked(NO_SHOW_LIMIT))

    def test_window(self):
        self.assertEqual(oldest_counted_day(datetime(2026, 11, 30, 9, 0)),
                         (datetime(2026, 11, 30) - timedelta(days=NO_SHOW_DAYS - 1)).strftime("%Y-%m-%d"))


if __name__ == "__main__":
    unittest.main()
