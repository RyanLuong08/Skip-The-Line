import unittest

from models import Order, db
from tests.helpers import AppTestCase


class TestStatsApi(AppTestCase):
    def test_today(self):
        first = self.order([(self.curry_rice, 2)]).get_json()["id"]
        self.order([(self.tea, 1)], vendor="fengyun-tea-shop")
        self.move(first, "cooking")
        self.move(first, "ready")
        order = db.session.get(Order, first)
        self.assertIsNotNone(order.cooking_at)
        self.assertGreaterEqual(order.ready_at, order.cooking_at)

        data = self.client.get("/api/stats").get_json()
        self.assertEqual((data["totals"]["orders"], data["totals"]["revenue"]), (2, 170))
        self.assertEqual(sum(h["orders"] for h in data["by_hour"]), 2)
        self.assertEqual({v["name"] for v in data["vendors"]}, {"Love Curry", "Tea Shop"})
        self.assertIsNotNone(data["totals"]["avg_wait_min"])

    def test_another_day_and_bad_day(self):
        self.order([(self.curry_rice, 1)])
        self.assertEqual(self.client.get("/api/stats?day=2000-01-01").get_json()["totals"]["orders"], 0)
        self.assertEqual(self.client.get("/api/stats?day=yesterday").status_code, 400)

    def test_page(self):
        self.assertIn("Orders per hour", self.client.get("/stats").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
