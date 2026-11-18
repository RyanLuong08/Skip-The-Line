import unittest
from datetime import datetime

from order_input import MAX_LINES, MAX_QTY, parse_items, parse_pickup

NOON = datetime(2026, 11, 19, 12, 0)


class TestParseItems(unittest.TestCase):
    def test_simple_order(self):
        self.assertEqual(parse_items([{"id": 3, "qty": 2}, {"id": 5}]), {3: 2, 5: 1})

    def test_same_dish_twice_is_added_up(self):
        self.assertEqual(parse_items([{"id": 3, "qty": 2}, {"id": 3, "qty": 1}]), {3: 3})

    def test_empty_or_wrong_type(self):
        for bad in (None, [], "3", {"id": 3}):
            with self.assertRaises(ValueError):
                parse_items(bad)

    def test_bad_ids(self):
        for bad in ("3", 3.5, None, True):
            with self.assertRaises(ValueError):
                parse_items([{"id": bad}])

    def test_bad_quantities(self):
        for bad in (0, -1, MAX_QTY + 1, "2", 1.5, True):
            with self.assertRaises(ValueError):
                parse_items([{"id": 1, "qty": bad}])

    def test_too_many_of_one_dish_across_lines(self):
        with self.assertRaises(ValueError):
            parse_items([{"id": 1, "qty": MAX_QTY}, {"id": 1, "qty": 1}])

    def test_too_many_lines(self):
        with self.assertRaises(ValueError):
            parse_items([{"id": i} for i in range(MAX_LINES + 1)])


class TestParsePickup(unittest.TestCase):
    def test_asap(self):
        for value in (None, "", "ASAP"):
            self.assertEqual(parse_pickup(value, NOON), "ASAP")

    def test_later_today(self):
        self.assertEqual(parse_pickup("12:30", NOON), "12:30")
        self.assertEqual(parse_pickup("13:5", NOON), "13:05")

    def test_a_few_minutes_late_is_fine(self):
        self.assertEqual(parse_pickup("11:56", NOON), "11:56")

    def test_past(self):
        with self.assertRaises(ValueError):
            parse_pickup("11:00", NOON)

    def test_too_far_ahead(self):
        with self.assertRaises(ValueError):
            parse_pickup("14:30", NOON)

    def test_nonsense(self):
        for bad in ("soon", "25:00", "12:60", "12", 1230, "12:30:00"):
            with self.assertRaises(ValueError):
                parse_pickup(bad, NOON)


if __name__ == "__main__":
    unittest.main()
