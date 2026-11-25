import unittest
from datetime import datetime

from stats import summarize


def at(hour, minute):
    return datetime(2026, 11, 25, hour, minute)


def order(vendor="curry", status="done", total=70, payment="counter", created=(12, 0), cooking=None, ready=None):
    return {"vendor": vendor, "status": status, "total": total, "payment": payment,
            "created_at": at(*created), "cooking_at": cooking and at(*cooking), "ready_at": ready and at(*ready)}


VENDORS = {"curry": {"name": "Love Curry", "avg_prep_min": 3}, "tea": {"name": "Tea Shop", "avg_prep_min": 2}}


class TestSummarize(unittest.TestCase):
    def test_no_orders(self):
        self.assertEqual(summarize([], VENDORS), {
            "totals": {"orders": 0, "cancelled": 0, "revenue": 0, "transfer": 0, "avg_wait_min": None},
            "by_hour": [], "vendors": []})

    def test_totals_leave_out_cancelled_orders(self):
        data = summarize([order(total=70), order(total=200, payment="transfer"),
                          order(total=999, status="cancelled")], VENDORS)
        self.assertEqual(data["totals"], {"orders": 2, "cancelled": 1, "revenue": 270, "transfer": 1,
                                          "avg_wait_min": None})

    def test_by_hour_fills_quiet_hours_with_zero(self):
        data = summarize([order(created=(11, 50)), order(created=(13, 5)), order(created=(13, 30))], VENDORS)
        self.assertEqual(data["by_hour"], [{"hour": 11, "orders": 1}, {"hour": 12, "orders": 0},
                                           {"hour": 13, "orders": 2}])

    def test_wait_and_cook_minutes(self):
        data = summarize([order(created=(12, 0), cooking=(12, 4), ready=(12, 9)),
                          order(created=(12, 0), cooking=(12, 10), ready=(12, 13)),
                          order(created=(12, 1), status="waiting")], VENDORS)
        self.assertEqual(data["totals"]["avg_wait_min"], 11.0)  # (9 + 13) / 2
        curry = data["vendors"][0]
        self.assertEqual((curry["avg_wait_min"], curry["avg_cook_min"]), (11.0, 4.0))  # cook (5 + 3) / 2
        self.assertIsNone(curry["measured_prep_min"])  # only 2 cooked orders

    def test_measured_prep_after_three_cooked_orders(self):
        cooked = [order(cooking=(12, 0), ready=(12, m)) for m in (2, 5, 6)]
        curry = summarize(cooked, VENDORS)["vendors"][0]
        self.assertEqual((curry["set_prep_min"], curry["measured_prep_min"]), (3, 5))  # median

    def test_vendors_busiest_first(self):
        data = summarize([order(vendor="tea"), order(vendor="curry"), order(vendor="curry"),
                          order(vendor="tea", status="cancelled")], VENDORS)
        self.assertEqual([(v["name"], v["orders"], v["cancelled"]) for v in data["vendors"]],
                         [("Love Curry", 2, 0), ("Tea Shop", 1, 1)])

    def test_unknown_vendor_still_listed(self):
        self.assertEqual(summarize([order(vendor="gone")], VENDORS)["vendors"][0]["name"], "gone")


if __name__ == "__main__":
    unittest.main()
