import unittest
from unittest import mock

import payment_rules
from tests.helpers import AppTestCase


class TestVendorApi(AppTestCase):
    def test_vendor_list(self):
        vendors = self.client.get("/api/vendor-list").get_json()
        self.assertEqual([v["slug"] for v in vendors], ["fengyun-love-curry", "fengyun-tea-shop"])

    def test_orders_by_ticket_and_only_for_this_vendor(self):
        self.order([(self.curry_rice, 1)])
        self.order([(self.curry_rice, 2)])
        self.order([(self.tea, 1)], vendor="fengyun-tea-shop")
        orders = self.client.get("/api/vendors/fengyun-love-curry/orders").get_json()["orders"]
        self.assertEqual([o["ticket"] for o in orders], [1, 2])

    def test_full_journey_of_an_order(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        for status in ("cooking", "ready", "done"):
            res = self.move(order_id, status)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json()["status"], status)
        # picked-up orders leave the dashboard
        self.assertEqual(self.client.get("/api/vendors/fengyun-love-curry/orders").get_json()["orders"], [])

    def test_cancel_a_new_order(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.assertEqual(self.move(order_id, "cancelled").status_code, 200)
        self.assertEqual(self.client.get("/api/my-orders").get_json()[0]["status"], "cancelled")

    def test_moves_that_are_not_allowed(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.assertEqual(self.move(order_id, "done").status_code, 409)
        self.assertEqual(self.move(order_id, "banana").status_code, 409)
        self.assertEqual(self.client.post(f"/api/orders/{order_id}/status", data="x").status_code, 409)
        self.assertEqual(self.move(9999, "cooking").status_code, 404)

    def test_counter_order_is_paid_when_picked_up(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.assertEqual(self.client.post(f"/api/orders/{order_id}/paid").status_code, 409)
        for status in ("cooking", "ready"):
            self.assertFalse(self.move(order_id, status).get_json()["paid"])
        self.assertTrue(self.move(order_id, "done").get_json()["paid"])

    def test_transfer_order_is_cooked_only_once_paid(self):
        bank = {"bank": "822 CTBC", "account": "000000000000"}
        with mock.patch.dict(payment_rules.BANK_ACCOUNTS, {"fengyun-love-curry": bank}):
            order_id = self.order([(self.curry_rice, 1)], payment="transfer", transfer_ref="12345").get_json()["id"]
        self.assertEqual(self.move(order_id, "cooking").status_code, 409)
        res = self.client.post(f"/api/orders/{order_id}/paid")
        self.assertEqual((res.status_code, res.get_json()["paid"]), (200, True))
        self.assertEqual(self.move(order_id, "cooking").status_code, 200)
        self.assertEqual(self.client.post("/api/orders/9999/paid").status_code, 404)

    def test_unknown_vendor(self):
        self.assertEqual(self.client.get("/api/vendors/nope/orders").status_code, 404)


class TestPages(AppTestCase):
    def test_student_page(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("css/app.css", html)
        self.assertIn('href="/" class="is-active"', html)

    def test_vendor_page(self):
        html = self.client.get("/vendor").get_data(as_text=True)
        self.assertIn('href="/vendor" class="is-active"', html)


if __name__ == "__main__":
    unittest.main()
