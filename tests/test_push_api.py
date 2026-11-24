import unittest
from unittest import mock

from models import Order, PushSubscription, db
from tests.helpers import AppTestCase

SUBSCRIPTION = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc",
                "keys": {"p256dh": "BNc...", "auth": "tBH..."}}


class TestPushApi(AppTestCase):
    def turn_push_on(self):
        self.app.config["VAPID_PUBLIC_KEY"] = "test-key"
        self.app.config["VAPID_KEY_FILE"] = "test.pem"

    def subscribe(self, data=SUBSCRIPTION):
        return self.client.post("/api/push/subscribe", json=data)

    def test_off_in_tests_by_default(self):
        self.assertIsNone(self.client.get("/api/push/key").get_json()["key"])
        self.assertEqual(self.subscribe().status_code, 503)

    def test_subscribe_links_this_browsers_orders(self):
        self.turn_push_on()
        before = self.order([(self.curry_rice, 1)]).get_json()["id"]
        self.assertEqual(self.subscribe().status_code, 200)
        after = self.order([(self.curry_rice, 1)]).get_json()["id"]
        other = self.order([(self.curry_rice, 1)], client=self.app.test_client()).get_json()["id"]
        sub_id = db.session.execute(db.select(PushSubscription.id)).scalar_one()
        self.assertEqual([db.session.get(Order, i).push_sub_id for i in (before, after, other)],
                         [sub_id, sub_id, None])

    def test_same_phone_twice_is_one_subscription(self):
        self.turn_push_on()
        self.subscribe()
        self.subscribe()
        self.assertEqual(db.session.execute(db.select(db.func.count(PushSubscription.id))).scalar(), 1)

    def test_bad_subscription(self):
        self.turn_push_on()
        self.assertEqual(self.subscribe({"endpoint": "https://evil.com/x", "keys": SUBSCRIPTION["keys"]}).status_code, 400)

    def test_phone_is_told_when_ready(self):
        self.turn_push_on()
        self.subscribe()
        order_id = self.order([(self.curry_rice, 1)]).get_json()["id"]
        with mock.patch("push_api.threading.Thread") as thread:
            self.move(order_id, "cooking")
            thread.assert_not_called()
            self.move(order_id, "ready")
        thread.assert_called_once()
        _app, key_file, _sub_id, info, message = thread.call_args.kwargs["args"]
        self.assertEqual((key_file, info), ("test.pem", SUBSCRIPTION))
        self.assertIn("#1 is ready", message)


if __name__ == "__main__":
    unittest.main()
