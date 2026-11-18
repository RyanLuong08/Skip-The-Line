import unittest
from datetime import datetime

from queue_rules import (ASAP, CANCELLED, COOKING, DONE, READY, WAITING, can_move,
                         estimate_wait_min, is_peak, next_ticket, pickup_slots, today, wait_level)


class TestTickets(unittest.TestCase):
    def test_first_ticket_of_the_day_is_one(self):
        self.assertEqual(next_ticket(None), 1)

    def test_next_ticket_follows_the_last(self):
        self.assertEqual(next_ticket(41), 42)

    def test_today_is_a_date_text(self):
        self.assertEqual(today(datetime(2026, 11, 19, 23, 59)), "2026-11-19")


class TestStatusMoves(unittest.TestCase):
    def test_normal_path(self):
        self.assertTrue(can_move(WAITING, COOKING))
        self.assertTrue(can_move(COOKING, READY))
        self.assertTrue(can_move(READY, DONE))

    def test_only_waiting_orders_can_be_cancelled(self):
        self.assertTrue(can_move(WAITING, CANCELLED))
        self.assertFalse(can_move(COOKING, CANCELLED))

    def test_no_skipping_or_going_back(self):
        self.assertFalse(can_move(WAITING, READY))
        self.assertFalse(can_move(READY, COOKING))
        self.assertFalse(can_move(DONE, WAITING))

    def test_unknown_status(self):
        self.assertFalse(can_move(WAITING, "eaten"))
        self.assertFalse(can_move("eaten", DONE))


class TestWait(unittest.TestCase):
    def test_wait_is_queue_times_minutes(self):
        self.assertEqual(estimate_wait_min(0, 3), 0)
        self.assertEqual(estimate_wait_min(4, 3), 12)

    def test_levels(self):
        self.assertEqual(wait_level(5), "low")
        self.assertEqual(wait_level(6), "mid")
        self.assertEqual(wait_level(15), "mid")
        self.assertEqual(wait_level(16), "high")


class TestTimes(unittest.TestCase):
    def test_peak_hours(self):
        self.assertTrue(is_peak(datetime(2026, 11, 19, 12, 0)))
        self.assertFalse(is_peak(datetime(2026, 11, 19, 12, 40)))  # the end is not included
        self.assertFalse(is_peak(datetime(2026, 11, 19, 15, 0)))
        self.assertTrue(is_peak(datetime(2026, 11, 19, 18, 0)))

    def test_slots_start_at_least_ten_minutes_away(self):
        slots = pickup_slots(datetime(2026, 11, 19, 12, 3))
        self.assertEqual(slots[:3], [ASAP, "12:20", "12:30"])
        self.assertEqual(len(slots), 10)

    def test_on_the_dot(self):
        self.assertEqual(pickup_slots(datetime(2026, 11, 19, 12, 0))[1], "12:10")

    def test_no_slots_after_midnight(self):
        slots = pickup_slots(datetime(2026, 11, 19, 23, 35))
        self.assertEqual(slots, [ASAP, "23:50"])


if __name__ == "__main__":
    unittest.main()
