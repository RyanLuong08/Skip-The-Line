import unittest

from models import Vendor, db, save_menu
from tests.helpers import AppTestCase


class TestMenuApi(AppTestCase):
    def test_halls_with_vendor_counts(self):
        halls = self.client.get("/api/halls").get_json()
        self.assertEqual([h["id"] for h in halls], ["fengyun", "shuimu", "xcb"])
        self.assertEqual([h["vendor_count"] for h in halls], [2, 0, 0])

    def test_vendors_start_with_no_queue(self):
        vendors = self.client.get("/api/vendors?hall=fengyun").get_json()
        self.assertEqual([v["name"] for v in vendors], ["Love Curry", "Tea Shop"])
        self.assertEqual((vendors[0]["queue"], vendors[0]["wait_min"], vendors[0]["wait_level"]), (0, 0, "low"))
        self.assertEqual(vendors[0]["dish_count"], 2)

    def test_wait_grows_with_the_queue(self):
        self.order([(self.curry_rice, 1)])
        self.order([(self.curry_rice, 1)])
        curry = self.client.get("/api/vendors?hall=fengyun").get_json()[0]
        self.assertEqual((curry["queue"], curry["wait_min"]), (2, 6))

    def test_ready_orders_no_longer_count(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.move(order_id, "cooking")
        self.move(order_id, "ready")
        self.assertEqual(self.client.get("/api/vendors?hall=fengyun").get_json()[0]["queue"], 0)

    def test_empty_hall_and_unknown_hall(self):
        self.assertEqual(self.client.get("/api/vendors?hall=shuimu").get_json(), [])
        self.assertEqual(self.client.get("/api/vendors?hall=mars").status_code, 404)

    def test_menu(self):
        data = self.client.get("/api/vendors/fengyun-love-curry/menu").get_json()
        self.assertEqual(data["vendor"]["name"], "Love Curry")
        self.assertEqual([i["name"] for i in data["items"]], ["Curry Rice", "Mystery Curry"])
        self.assertEqual(data["items"][0]["name_zh"], "咖哩飯")
        self.assertEqual(self.client.get("/api/vendors/nope/menu").status_code, 404)

    def test_now(self):
        data = self.client.get("/api/now").get_json()
        self.assertIn(data["peak"], (True, False))
        self.assertEqual(data["pickup_slots"][0], "ASAP")

    def test_reimporting_keeps_the_vendor_and_its_orders(self):
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        save_menu([{"slug": "fengyun-love-curry", "hall": "fengyun", "name": "Love Curry",
                    "name_zh": "喜番咖哩", "cuisine": "Japanese", "avg_prep_min": 4,
                    "items": [{"name": "Beef Curry", "name_zh": "", "price": 95, "calories": None,
                               "category": "rice", "vegetarian": False}]}])
        vendors = db.session.execute(db.select(Vendor)).scalars().all()
        self.assertEqual(len(vendors), 2)
        menu = self.client.get("/api/vendors/fengyun-love-curry/menu").get_json()
        self.assertEqual([i["name"] for i in menu["items"]], ["Beef Curry"])
        self.assertEqual(menu["vendor"]["avg_prep_min"], 4)
        # the old order still has its own copy of the dish
        orders = self.client.get("/api/vendors/fengyun-love-curry/orders").get_json()["orders"]
        self.assertEqual(orders[0]["id"], order_id)
        self.assertEqual(orders[0]["lines"][0]["name"], "Curry Rice")


if __name__ == "__main__":
    unittest.main()
