import unittest

from payment_rules import (COUNTER, COUNTER_LIMIT, TRANSFER, can_start_cooking, check_payment,
                           counter_allowed, parse_transfer_ref)


class TestCounterLimit(unittest.TestCase):
    def test_under_the_limit_only(self):
        self.assertTrue(counter_allowed(COUNTER_LIMIT - 1))
        self.assertFalse(counter_allowed(COUNTER_LIMIT))  # NT$200 exactly is not "under 200"
        self.assertFalse(counter_allowed(COUNTER_LIMIT + 50))

    def test_pay_at_pickup(self):
        self.assertEqual(check_payment(COUNTER, 199, unpriced=False, has_account=False), "")
        # a dish without a price is fine: the student pays for it at the counter
        self.assertEqual(check_payment(COUNTER, 70, unpriced=True, has_account=False), "")
        with self.assertRaises(ValueError):
            check_payment(COUNTER, 200, unpriced=False, has_account=True)


class TestTransfer(unittest.TestCase):
    def test_transfer(self):
        self.assertEqual(check_payment(TRANSFER, 350, False, True, " 01234 "), "01234")

    def test_vendor_without_an_account(self):
        with self.assertRaises(ValueError):
            check_payment(TRANSFER, 350, False, False, "12345")

    def test_unknown_amount(self):
        with self.assertRaises(ValueError):
            check_payment(TRANSFER, 350, True, True, "12345")

    def test_last_five_digits(self):
        self.assertEqual(parse_transfer_ref("00042"), "00042")
        for bad in (None, "", "1234", "123456", "12a45", 12345, "１２３４５"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                parse_transfer_ref(bad)

    def test_no_choice_or_nonsense(self):
        for bad in (None, "", "cash", 1):
            with self.assertRaises(ValueError):
                check_payment(bad, 100, False, True, "12345")

    def test_cook_transfer_orders_only_once_paid(self):
        self.assertFalse(can_start_cooking(TRANSFER, paid=False))
        self.assertTrue(can_start_cooking(TRANSFER, paid=True))
        self.assertTrue(can_start_cooking(COUNTER, paid=False))


if __name__ == "__main__":
    unittest.main()


class TestBankAccountsFile(unittest.TestCase):
    ACCOUNT = {"bank": "822 CTBC", "account": "123456789012", "holder": "Team"}

    def tearDown(self):
        import payment_rules
        payment_rules.use_bank_accounts(None, {})

    def test_default_and_per_vendor(self):
        from payment_rules import bank_account, parse_bank_accounts, use_bank_accounts
        other = dict(self.ACCOUNT, account="999")
        default, vendors = parse_bank_accounts({"default": self.ACCOUNT, "vendors": {"xcb-bistro": other}})
        use_bank_accounts(default, vendors)
        self.assertEqual(bank_account("xcb-bistro")["account"], "999")
        self.assertEqual(bank_account("fengyun-love-curry")["account"], "123456789012")

    def test_no_default_means_transfer_off(self):
        from payment_rules import parse_bank_accounts
        self.assertEqual(parse_bank_accounts({}), (None, {}))

    def test_missing_fields(self):
        from payment_rules import parse_bank_accounts
        for bad in ([], {"default": {"bank": "x"}}, {"default": dict(self.ACCOUNT, holder=" ")},
                    {"vendors": ["x"]}, {"vendors": {"a": "123"}}):
            with self.assertRaises(ValueError):
                parse_bank_accounts(bad)
