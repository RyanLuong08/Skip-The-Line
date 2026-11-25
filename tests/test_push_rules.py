import unittest

from push_rules import parse_subscription, ready_message

KEYS = {"p256dh": "BNc...", "auth": "tBH..."}


class TestSubscription(unittest.TestCase):
    def test_real_push_services(self):
        for endpoint in ("https://fcm.googleapis.com/fcm/send/abc",
                         "https://updates.push.services.mozilla.com/wpush/v2/abc",
                         "https://web.push.apple.com/QH8abc",
                         "https://wns2-par02p.notify.windows.com/w/?token=abc"):
            self.assertEqual(parse_subscription({"endpoint": endpoint, "keys": KEYS}),
                             (endpoint, "BNc...", "tBH..."))

    def test_other_addresses_are_refused(self):
        # otherwise anyone could make the server send requests to any address
        for endpoint in ("http://fcm.googleapis.com/fcm/send/abc", "https://localhost/x",
                         "https://evil.com/fcm.googleapis.com", "https://fcm.googleapis.com.evil.com/x",
                         "https://192.168.1.1/", "https://fcm.googleapis.com/" + "a" * 600, None, 5):
            with self.assertRaises(ValueError, msg=endpoint):
                parse_subscription({"endpoint": endpoint, "keys": KEYS})

    def test_bad_shapes(self):
        good = "https://fcm.googleapis.com/fcm/send/abc"
        for data in (None, "x", {}, {"endpoint": good}, {"endpoint": good, "keys": {"p256dh": "x"}},
                     {"endpoint": good, "keys": {"p256dh": "", "auth": "y"}}):
            with self.assertRaises(ValueError):
                parse_subscription(data)


class TestMessage(unittest.TestCase):
    def test_ready_message(self):
        message = ready_message(12, "Love Curry")
        self.assertEqual(message["title"], "#12 is ready!")
        self.assertIn("Love Curry", message["body"])


if __name__ == "__main__":
    unittest.main()
