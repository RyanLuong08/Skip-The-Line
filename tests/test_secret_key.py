import unittest

from secret_key import MIN_KEY_LENGTH, choose_secret_key


class TestChooseSecretKey(unittest.TestCase):
    def test_environment_wins(self):
        self.assertEqual(choose_secret_key(" from-env ", "x" * 64), ("from-env", False))

    def test_saved_key_is_reused(self):
        self.assertEqual(choose_secret_key(None, "k" * 64 + "\n"), ("k" * 64, False))

    def test_new_key_when_there_is_none_or_it_is_too_short(self):
        for saved in (None, "", "short"):
            key, must_save = choose_secret_key(None, saved)
            self.assertTrue(must_save)
            self.assertGreaterEqual(len(key), MIN_KEY_LENGTH)


if __name__ == "__main__":
    unittest.main()
