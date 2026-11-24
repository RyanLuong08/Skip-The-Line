import io
import unittest

from menu_import import DATA_DIR, find_hall, read_all_csv, read_menu_csv, slug, to_number

HEADER = ("id,store_name,store_name_english,location,location_english,dish_name,price,calories,"
          "protein,carbs,fat,is_vegetarian,is_official,cuisine,is_combo,category,EnglishName,ChineseName\n")


def csv_text(*rows):
    return io.StringIO(HEADER + "".join(row + "\n" for row in rows))


class TestHelpers(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slug("MN Tea Time & Tea Lounge"), "mn-tea-time-tea-lounge")

    def test_to_number(self):
        self.assertEqual(to_number("80"), 80)
        self.assertEqual(to_number("325.45"), 325.45)
        self.assertIsNone(to_number(""))
        self.assertIsNone(to_number("n/a"))
        self.assertIsNone(to_number(None))

    def test_find_hall(self):
        self.assertEqual(find_hall("Fengyun Building"), "fengyun")
        self.assertEqual(find_hall("Shuimu Student Center"), "shuimu")
        self.assertEqual(find_hall("XCB 2F"), "xcb")
        self.assertIsNone(find_hall("Taipei 101"))


class TestReadMenu(unittest.TestCase):
    def test_rows_are_grouped_by_vendor(self):
        vendors, skipped = read_menu_csv(csv_text(
            "1,喜番咖哩,Love Curry,風雲樓,Fengyun Building,咖哩飯 Curry Rice,70,500,,,,FALSE,TRUE,Japanese,FALSE,rice,Curry Rice,咖哩飯",
            "2,喜番咖哩,Love Curry,風雲樓,Fengyun Building,蔬菜咖哩 Veg Curry,,,,,,TRUE,TRUE,Japanese,FALSE,rice,Veg Curry,蔬菜咖哩",
            "3,茶,Tea Shop,風雲樓,Fengyun Building,紅茶 Black Tea,30,,,,,TRUE,TRUE,Drinks,FALSE,drinks,Black Tea,紅茶"))
        self.assertEqual(skipped, 0)
        self.assertEqual([v["name"] for v in vendors], ["Love Curry", "Tea Shop"])
        curry = vendors[0]
        self.assertEqual(curry["slug"], "fengyun-love-curry")
        self.assertEqual(curry["name_zh"], "喜番咖哩")
        self.assertEqual(curry["items"][0], {"name": "Curry Rice", "name_zh": "咖哩飯", "price": 70,
                                             "calories": 500, "category": "rice", "vegetarian": False})
        self.assertIsNone(curry["items"][1]["price"])
        self.assertTrue(curry["items"][1]["vegetarian"])

    def test_rows_without_a_known_hall_are_skipped(self):
        vendors, skipped = read_menu_csv(csv_text(
            "1,x,Somewhere,x,Taipei,Dish,10,,,,,FALSE,TRUE,x,FALSE,rice,Dish,菜"))
        self.assertEqual((vendors, skipped), ([], 1))

    def test_the_real_fengyun_file(self):
        vendors, skipped = read_all_csv(DATA_DIR)
        fengyun = [v for v in vendors if v["hall"] == "fengyun"]
        self.assertEqual(len(fengyun), 10)
        self.assertEqual(sum(len(v["items"]) for v in fengyun), 286)
        self.assertEqual(skipped, 0)

    def test_the_real_xcb_file(self):
        vendors, _ = read_all_csv(DATA_DIR)
        xcb = [v for v in vendors if v["hall"] == "xcb"]
        self.assertEqual([v["name"] for v in xcb],
                         ["Haofu Curry", "Ichi-Ban", "Han Cheng Cuisine", "Su Beef Noodles", "Bao So Hard", "Bistro"])
        self.assertEqual(sum(len(v["items"]) for v in xcb), 162)
        self.assertTrue(all(item["price"] is not None for v in xcb for item in v["items"]))


if __name__ == "__main__":
    unittest.main()
