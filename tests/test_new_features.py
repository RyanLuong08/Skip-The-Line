"""Sold out, pause, search, order again, no-shows, board and QR."""

import unittest
from datetime import timedelta

from models import Order, db
from noshow_rules import NO_SHOW_AFTER_MIN, NO_SHOW_LIMIT
from queue_rules import now
from tests.helpers import AppTestCase


class TestSoldOutAndPause(AppTestCase):
    def test_sold_out_today_only(self):
        res = self.client.post(f"/api/items/{self.curry_rice.id}/sold-out", json={"sold_out": True})
        self.assertTrue(res.get_json()["sold_out"])
        menu = self.client.get("/api/vendors/fengyun-love-curry/menu").get_json()["items"]
        self.assertTrue(menu[0]["sold_out"])
        refused = self.order([(self.curry_rice, 1)])
        self.assertEqual(refused.status_code, 400)
        self.assertIn("sold out", refused.get_json()["error"])
        # tomorrow it is back by itself
        self.curry_rice.sold_out_day = "2000-01-01"
        db.session.commit()
        self.assertEqual(self.order([(self.curry_rice, 1)]).status_code, 201)

    def test_back_on(self):
        self.client.post(f"/api/items/{self.curry_rice.id}/sold-out", json={"sold_out": True})
        self.client.post(f"/api/items/{self.curry_rice.id}/sold-out", json={"sold_out": False})
        self.assertEqual(self.order([(self.curry_rice, 1)]).status_code, 201)

    def test_pause(self):
        res = self.client.post("/api/vendors/fengyun-love-curry/pause", json={"paused": True})
        self.assertTrue(res.get_json()["paused"])
        vendors = self.client.get("/api/vendors?hall=fengyun").get_json()
        self.assertTrue(next(v for v in vendors if v["slug"] == "fengyun-love-curry")["paused"])
        self.assertEqual(self.order([(self.curry_rice, 1)]).status_code, 409)
        self.assertEqual(self.order([(self.tea, 1)], vendor="fengyun-tea-shop").status_code, 201)  # others fine
        self.client.post("/api/vendors/fengyun-love-curry/pause", json={"paused": False})
        self.assertEqual(self.order([(self.curry_rice, 1)]).status_code, 201)

    def test_bad_requests_and_pin(self):
        self.assertEqual(self.client.post("/api/vendors/fengyun-love-curry/pause", json={"paused": "yes"}).status_code, 400)
        self.assertEqual(self.client.post(f"/api/items/{self.tea.id}/sold-out", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/items/999/sold-out", json={"sold_out": True}).status_code, 404)
        self.assertEqual(self.client.post("/api/vendors/nope/pause", json={"paused": True}).status_code, 404)
        student = self.app.test_client()
        self.assertEqual(student.post("/api/vendors/fengyun-love-curry/pause", json={"paused": True}).status_code, 401)
        self.assertEqual(student.post(f"/api/items/{self.tea.id}/sold-out", json={"sold_out": True}).status_code, 401)


class TestSearch(AppTestCase):
    def search(self, **args):
        return self.client.get("/api/search", query_string=args).get_json()

    def test_words_match_dish_vendor_and_chinese(self):
        self.assertEqual([d["name"] for d in self.search(q="mystery curry")], ["Mystery Curry"])
        self.assertEqual([d["name"] for d in self.search(q="咖哩飯")], ["Curry Rice"])
        self.assertEqual({d["name"] for d in self.search(q="RICE")}, {"Curry Rice", "Mystery Curry"})  # category
        self.assertEqual({d["name"] for d in self.search(q="love")}, {"Curry Rice", "Mystery Curry"})
        found = self.search(q="tea")[0]
        self.assertEqual((found["vendor"]["slug"], found["vendor"]["hall"]), ("fengyun-tea-shop", "Fengyun"))

    def test_filters_and_order(self):
        self.tea.vegetarian = True
        db.session.commit()
        self.assertEqual([d["name"] for d in self.search(veg="1")], ["Black Tea"])
        # cheapest first; a dish without a price never passes a price filter
        self.assertEqual([d["name"] for d in self.search(max_price="80")], ["Black Tea", "Curry Rice"])
        self.assertEqual(self.client.get("/api/search?max_price=cheap").status_code, 400)

    def test_nothing_asked_and_sold_out(self):
        self.assertEqual(self.search(), [])
        self.client.post(f"/api/items/{self.tea.id}/sold-out", json={"sold_out": True})
        self.assertEqual(self.search(q="tea"), [])


class TestOrderAgain(AppTestCase):
    def test_recent_orders_newest_first_without_repeats(self):
        self.order([(self.curry_rice, 2)])
        self.order([(self.tea, 1)], vendor="fengyun-tea-shop")
        self.order([(self.curry_rice, 2)])  # same as the first: shown once
        recent = self.client.get("/api/my-orders/recent").get_json()
        self.assertEqual([o["vendor"]["slug"] for o in recent], ["fengyun-love-curry", "fengyun-tea-shop"])
        self.assertEqual(recent[0]["lines"][0]["item_id"], self.curry_rice.id)

    def test_cancelled_and_other_days(self):
        first = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.client.post(f"/api/my-orders/{first}/cancel")
        self.order([(self.tea, 1)], vendor="fengyun-tea-shop")
        db.session.execute(db.update(Order).values(day="2000-01-01"))  # yesterday's orders count too
        db.session.commit()
        self.assertEqual([o["vendor"]["slug"] for o in self.client.get("/api/my-orders/recent").get_json()],
                         ["fengyun-tea-shop"])

    def test_session_lasts(self):
        self.order([(self.curry_rice, 1)])
        cookie = self.client.get_cookie("session")
        self.assertIsNotNone(cookie.expires)  # survives closing the browser


class TestNoShow(AppTestCase):
    def ready_order(self, minutes_ago=NO_SHOW_AFTER_MIN):
        order_id = self.order([(self.tea, 1)], vendor="fengyun-tea-shop").get_json()["id"]
        self.move(order_id, "cooking")
        self.move(order_id, "ready")
        order = db.session.get(Order, order_id)
        order.ready_at = now() - timedelta(minutes=minutes_ago)
        db.session.commit()
        return order_id

    def test_too_early(self):
        order_id = self.ready_order(minutes_ago=2)
        res = self.move(order_id, "no_show")
        self.assertEqual(res.status_code, 409)
        listed = self.client.get("/api/vendors/fengyun-tea-shop/orders").get_json()["orders"][0]
        self.assertEqual(listed["no_show_in"], NO_SHOW_AFTER_MIN - 2)

    def test_counter_blocked_after_the_limit(self):
        for i in range(NO_SHOW_LIMIT):
            self.assertEqual(self.client.get("/api/me").get_json()["no_shows"], i)
            self.assertEqual(self.move(self.ready_order(), "no_show").status_code, 200)
        me = self.client.get("/api/me").get_json()
        self.assertEqual((me["no_shows"], me["counter_blocked"]), (NO_SHOW_LIMIT, True))
        refused = self.order([(self.curry_rice, 1)])
        self.assertEqual(refused.status_code, 403)
        # another student (another browser) is not affected
        self.assertEqual(self.order([(self.curry_rice, 1)], client=self.app.test_client()).status_code, 201)

    def test_old_no_shows_expire(self):
        for _ in range(NO_SHOW_LIMIT):
            self.move(self.ready_order(), "no_show")
        db.session.execute(db.update(Order).values(day="2000-01-01"))
        db.session.commit()
        self.assertFalse(self.client.get("/api/me").get_json()["counter_blocked"])

    def test_no_show_is_final_and_not_on_the_dashboard(self):
        order_id = self.ready_order()
        self.move(order_id, "no_show")
        self.assertEqual(self.move(order_id, "done").status_code, 409)
        self.assertEqual(self.client.get("/api/vendors/fengyun-tea-shop/orders").get_json()["orders"], [])
        self.assertEqual(self.client.get("/api/my-orders").get_json()[0]["status"], "no_show")


class TestScreens(AppTestCase):
    def test_board(self):
        first = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.order([(self.curry_rice, 1)])
        self.move(first, "cooking")
        self.move(first, "ready")
        data = self.app.test_client().get("/api/board?hall=fengyun").get_json()  # no PIN needed
        curry = data["vendors"][0]
        self.assertEqual((curry["name"], curry["ready"], curry["cooking"], curry["waiting"]), ("Love Curry", [1], [], 1))
        self.assertEqual(data["vendors"][1]["name"], "Tea Shop")  # quiet vendors last
        self.assertEqual(self.client.get("/api/board?hall=mars").status_code, 404)
        self.assertIn("board-grid", self.client.get("/board").get_data(as_text=True))

    def test_qr_page_shows_the_address(self):
        html = self.client.get("/qr", base_url="https://abc.ngrok-free.app").get_data(as_text=True)
        self.assertIn("https://abc.ngrok-free.app/", html)
        html = self.client.get("/qr", base_url="http://localhost:5000").get_data(as_text=True)
        self.assertNotIn("http://localhost:5000/<", html)  # swapped for the laptop's Wi-Fi address

    def test_qr_image(self):
        try:
            import qrcode  # noqa: F401
        except ImportError:
            self.skipTest("qrcode is not installed")
        res = self.client.get("/qr.svg", base_url="https://abc.ngrok-free.app")
        self.assertEqual(res.mimetype, "image/svg+xml")
        self.assertIn("<svg", res.get_data(as_text=True))


class TestLanguage(AppTestCase):
    def test_every_page_loads_the_translations(self):
        for page in ("/", "/vendor", "/stats", "/board", "/qr", "/vendor/login"):
            client = self.app.test_client() if page == "/vendor/login" else self.client
            self.assertIn("js/i18n.js", client.get(page).get_data(as_text=True), page)

    def test_both_languages_have_the_same_keys(self):
        import re
        from pathlib import Path
        text = (Path(__file__).resolve().parent.parent / "static" / "js" / "i18n.js").read_text(encoding="utf-8")
        en, zh = text.split("  zh: {")
        keys = lambda part: set(re.findall(r"\b([a-z_0-9]+): \"", part))
        self.assertEqual(keys(en.split("en: {")[1]), keys(zh))

    def test_keys_used_in_pages_exist(self):
        import re
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        text = (root / "static" / "js" / "i18n.js").read_text(encoding="utf-8")
        known = set(re.findall(r"\b([a-z_0-9]+): \"", text))
        for page in (root / "templates").glob("*.html"):
            html = page.read_text(encoding="utf-8")
            used = set(re.findall(r'data-i18n(?:-placeholder|-label)?="([a-z_0-9]+)"', html))
            used |= set(re.findall(r'\bt\("([a-z_0-9]+)"', html))
            used = {k for k in used if not k.endswith("_")}  # t("st_" + status): checked below
            self.assertEqual(used - known, set(), page.name)
        for status in ("waiting", "cooking", "ready", "done", "cancelled", "no_show"):
            self.assertIn(f"st_{status}", known)


if __name__ == "__main__":
    unittest.main()
