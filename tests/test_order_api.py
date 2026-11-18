import unittest

from models import Order, db
from tests.helpers import AppTestCase


class TestPlaceOrder(AppTestCase):
    def test_order_gets_ticket_one_and_the_right_total(self):
        res = self.order([(self.curry_rice, 2)])
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual((data["ticket"], data["status"], data["total"], data["ahead"]), (1, "waiting", 140, 0))
        self.assertEqual(data["lines"], [{"name": "Curry Rice", "price": 70, "qty": 2}])
        self.assertFalse(data["unpriced"])

    def test_tickets_count_up_per_vendor(self):
        self.assertEqual(self.order([(self.curry_rice, 1)]).get_json()["ticket"], 1)
        second = self.order([(self.curry_rice, 1)]).get_json()
        self.assertEqual((second["ticket"], second["ahead"]), (2, 1))
        # another vendor has its own numbers
        self.assertEqual(self.order([(self.tea, 1)], vendor="fengyun-tea-shop").get_json()["ticket"], 1)

    def test_tickets_start_again_the_next_day(self):
        self.order([(self.curry_rice, 1)])
        db.session.execute(db.update(Order).values(day="2000-01-01"))
        db.session.commit()
        self.assertEqual(self.order([(self.curry_rice, 1)]).get_json()["ticket"], 1)

    def test_dish_without_a_price(self):
        data = self.order([(self.curry_rice, 1), (self.mystery, 1)]).get_json()
        self.assertEqual(data["total"], 70)
        self.assertTrue(data["unpriced"])

    def test_the_browser_cannot_set_the_price(self):
        res = self.client.post("/api/orders", json={
            "vendor": "fengyun-love-curry", "items": [{"id": self.curry_rice.id, "qty": 1, "price": 1}]})
        self.assertEqual(res.get_json()["total"], 70)

    def test_dish_from_another_vendor_is_refused(self):
        res = self.order([(self.tea, 1)], vendor="fengyun-love-curry")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(db.session.execute(db.select(db.func.count(Order.id))).scalar(), 0)

    def test_bad_requests(self):
        self.assertEqual(self.order([(self.curry_rice, 1)], vendor="nope").status_code, 404)
        self.assertEqual(self.order([]).status_code, 400)
        self.assertEqual(self.order([(self.curry_rice, 99)]).status_code, 400)
        self.assertEqual(self.order([(self.curry_rice, 1)], pickup="yesterday").status_code, 400)
        self.assertEqual(self.client.post("/api/orders", data="hello").status_code, 400)


class TestMyOrders(AppTestCase):
    def test_nothing_yet(self):
        self.assertEqual(self.client.get("/api/my-orders").get_json(), [])

    def test_shows_only_this_browsers_orders_newest_first(self):
        self.order([(self.curry_rice, 1)])
        self.order([(self.tea, 1)], vendor="fengyun-tea-shop")
        other = self.app.test_client()  # another student's browser
        self.order([(self.curry_rice, 1)], client=other)

        mine = self.client.get("/api/my-orders").get_json()
        self.assertEqual([o["vendor"]["name"] for o in mine], ["Tea Shop", "Love Curry"])
        self.assertEqual(len(other.get("/api/my-orders").get_json()), 1)

    def test_ahead_goes_down_as_the_vendor_works(self):
        first = self.order([(self.curry_rice, 1)], client=self.app.test_client()).get_json()
        self.order([(self.curry_rice, 1)])
        self.assertEqual(self.client.get("/api/my-orders").get_json()[0]["ahead"], 1)
        self.move(first["id"], "cooking")
        self.assertEqual(self.client.get("/api/my-orders").get_json()[0]["ahead"], 1)  # still being made
        self.move(first["id"], "ready")
        self.assertEqual(self.client.get("/api/my-orders").get_json()[0]["ahead"], 0)


if __name__ == "__main__":
    unittest.main()
