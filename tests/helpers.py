"""Shared set-up for the tests that need the app and a database."""

import unittest

from app import create_app
from models import MenuItem, Vendor, db


class AppTestCase(unittest.TestCase):
    """Each test gets a fresh app with an empty in-memory database and a tiny menu:
    Love Curry (2 dishes, one without a price) and Tea Shop (1 dish)."""

    def setUp(self):
        self.app = create_app("sqlite:///:memory:", load_menu=False)
        self.context = self.app.app_context()
        self.context.push()
        curry = Vendor(slug="fengyun-love-curry", hall="fengyun", name="Love Curry",
                       name_zh="喜番咖哩", cuisine="Japanese", avg_prep_min=3)
        curry.items = [MenuItem(name="Curry Rice", name_zh="咖哩飯", price=70, category="rice"),
                       MenuItem(name="Mystery Curry", price=None, category="rice")]
        tea = Vendor(slug="fengyun-tea-shop", hall="fengyun", name="Tea Shop", avg_prep_min=2)
        tea.items = [MenuItem(name="Black Tea", price=30, category="drinks")]
        db.session.add_all([curry, tea])
        db.session.commit()
        self.curry_rice, self.mystery = curry.items
        self.tea = tea.items[0]
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def order(self, items, vendor="fengyun-love-curry", pickup="ASAP", client=None,
              payment="counter", transfer_ref=None):
        """Place an order; items is a list of (MenuItem, qty). Returns the response."""
        return (client or self.client).post("/api/orders", json={
            "vendor": vendor, "pickup": pickup, "payment": payment, "transfer_ref": transfer_ref,
            "items": [{"id": item.id, "qty": qty} for item, qty in items]})

    def move(self, order_id, status):
        return self.client.post(f"/api/orders/{order_id}/status", json={"status": status})
