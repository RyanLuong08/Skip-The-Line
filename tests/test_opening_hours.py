import unittest
from datetime import datetime

from opening_hours import (is_open, next_opening, open_at, parse_hours, pickup_allowed,
                           vendor_pickup_slots)
from queue_rules import ASAP

LUNCH_DINNER = parse_hours("10:30-14:00, 16:30-19:30")


def at(hhmm):
    hours, minutes = map(int, hhmm.split(":"))
    return datetime(2026, 11, 19, hours, minutes)


class TestParse(unittest.TestCase):
    def test_lunch_and_dinner(self):
        self.assertEqual(LUNCH_DINNER, [(630, 840), (990, 1170)])

    def test_other_ways_of_writing_it(self):
        self.assertEqual(parse_hours("16:30-19:30;10:30-14:00"), LUNCH_DINNER)  # any order, ";" ok
        self.assertEqual(parse_hours("10:30-14:00，16:30-19:30"), LUNCH_DINNER)  # Chinese comma
        self.assertEqual(parse_hours("7:00-24:00"), [(420, 1440)])

    def test_unknown_hours(self):
        self.assertEqual(parse_hours(""), [])
        self.assertEqual(parse_hours(None), [])

    def test_nonsense(self):
        for bad in ("lunch", "10:30", "10:30-25:00", "14:00-10:30", "10:30-14:00,", "10-14"):
            with self.assertRaises(ValueError, msg=bad):
                parse_hours(bad)


class TestOpen(unittest.TestCase):
    def test_open_and_closed(self):
        self.assertTrue(is_open(LUNCH_DINNER, at("10:30")))
        self.assertTrue(is_open(LUNCH_DINNER, at("13:59")))
        self.assertFalse(is_open(LUNCH_DINNER, at("14:00")))  # closing time is not included
        self.assertFalse(is_open(LUNCH_DINNER, at("15:00")))
        self.assertFalse(is_open(LUNCH_DINNER, at("22:00")))

    def test_unknown_hours_count_as_open(self):
        self.assertTrue(is_open([], at("03:00")))
        self.assertTrue(open_at([], 0))

    def test_next_opening(self):
        self.assertEqual(next_opening(LUNCH_DINNER, at("08:00")), "10:30")
        self.assertEqual(next_opening(LUNCH_DINNER, at("15:00")), "16:30")
        self.assertIsNone(next_opening(LUNCH_DINNER, at("20:00")))


class TestPickup(unittest.TestCase):
    def test_asap_only_while_open(self):
        self.assertTrue(pickup_allowed(LUNCH_DINNER, ASAP, at("12:00")))
        self.assertFalse(pickup_allowed(LUNCH_DINNER, ASAP, at("15:00")))

    def test_a_time_when_it_is_open(self):
        self.assertTrue(pickup_allowed(LUNCH_DINNER, "16:30", at("15:00")))
        self.assertFalse(pickup_allowed(LUNCH_DINNER, "14:10", at("13:00")))

    def test_slots_near_closing_time(self):
        self.assertEqual(vendor_pickup_slots(LUNCH_DINNER, at("13:35")), [ASAP, "13:50"])

    def test_order_ahead_before_it_opens(self):
        slots = vendor_pickup_slots(LUNCH_DINNER, at("15:55"))
        self.assertEqual(slots[:3], ["16:30", "16:40", "16:50"])  # no ASAP: it's closed now

    def test_closed_for_the_day(self):
        self.assertEqual(vendor_pickup_slots(LUNCH_DINNER, at("20:00")), [])


if __name__ == "__main__":
    unittest.main()
