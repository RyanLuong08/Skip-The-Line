import unittest

from staff_auth import MIN_PIN_LENGTH, PIN_DIGITS, choose_pin, pin_matches, safe_next
from tests.helpers import AppTestCase


class TestPinRules(unittest.TestCase):
    def test_environment_wins(self):
        self.assertEqual(choose_pin(" 9876 ", "111111"), ("9876", False))

    def test_saved_pin_is_reused(self):
        self.assertEqual(choose_pin(None, "482913\n"), ("482913", False))

    def test_new_pin_when_none_or_too_short(self):
        for saved in (None, "", "12"):
            pin, must_save = choose_pin(None, saved)
            self.assertTrue(must_save)
            self.assertEqual(len(pin), PIN_DIGITS)
            self.assertTrue(pin.isdigit())
        self.assertGreaterEqual(PIN_DIGITS, MIN_PIN_LENGTH)

    def test_pin_matches(self):
        self.assertTrue(pin_matches("1234", "1234"))
        self.assertTrue(pin_matches(" 1234 ", "1234"))
        self.assertFalse(pin_matches("1235", "1234"))
        self.assertFalse(pin_matches("", "1234"))
        self.assertFalse(pin_matches(None, "1234"))
        self.assertFalse(pin_matches("1234", None))

    def test_only_local_pages_after_login(self):
        self.assertEqual(safe_next("/vendor?v=xcb-bistro"), "/vendor?v=xcb-bistro")
        for bad in ("https://evil.example", "//evil.example", "evil", "", None):
            self.assertIsNone(safe_next(bad))


class TestStaffPages(AppTestCase):
    def setUp(self):
        super().setUp()
        self.student = self.app.test_client()  # never typed the PIN

    def test_students_are_sent_to_the_pin_page(self):
        res = self.student.get("/vendor?v=fengyun-love-curry")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/vendor/login?next=/vendor?v%3Dfengyun-love-curry", res.headers["Location"])
        self.assertEqual(self.student.get("/stats").status_code, 302)

    def test_vendor_apis_say_401_without_the_pin(self):
        order_id = self.order([(self.curry_rice, 1)], client=self.student).get_json()["id"]
        for res in (self.student.get("/api/vendor-list"),
                    self.student.get("/api/vendors/fengyun-love-curry/orders"),
                    self.student.post(f"/api/orders/{order_id}/status", json={"status": "cooking"}),
                    self.student.post(f"/api/orders/{order_id}/paid"),
                    self.student.get("/api/stats")):
            self.assertEqual(res.status_code, 401)
        # ...but the student can still order, see and cancel their own order
        self.assertEqual(len(self.student.get("/api/my-orders").get_json()), 1)
        self.assertEqual(self.student.post(f"/api/my-orders/{order_id}/cancel").status_code, 200)

    def test_wrong_pin(self):
        res = self.login(self.student, pin="0000")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Wrong PIN", res.get_data(as_text=True))
        self.assertEqual(self.student.get("/api/vendor-list").status_code, 401)

    def test_right_pin_goes_back_to_the_page_asked_for(self):
        res = self.student.post("/vendor/login", data={"pin": "1234", "next": "/stats"})
        self.assertEqual((res.status_code, res.headers["Location"]), (302, "/stats"))
        self.assertEqual(self.student.get("/api/vendor-list").status_code, 200)

    def test_never_sent_to_another_website(self):
        res = self.student.post("/vendor/login", data={"pin": "1234", "next": "https://evil.example"})
        self.assertEqual(res.headers["Location"], "/vendor")

    def test_log_out(self):
        self.client.post("/vendor/logout")
        self.assertEqual(self.client.get("/api/vendor-list").status_code, 401)

    def test_staff_links_only_for_staff(self):
        self.assertIn('href="/stats"', self.client.get("/vendor").get_data(as_text=True))
        self.assertNotIn('href="/stats"', self.student.get("/").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
