"""Read the menu CSV files in data/ (owner: B).

read_menu_csv() is plain Python with no database, so it is easy to test.
save_menu() in models.py puts the result into the database.

To add Shuimu or XCB: save the sheet as a CSV with the SAME columns as data/Fengyun.csv,
put it in data/, and run:  python import_menu.py
The dining hall is worked out from the "location_english" column.
"""

import csv
import re
from pathlib import Path

from opening_hours import parse_hours

DATA_DIR = Path(__file__).resolve().parent / "data"

# The three dining areas, in the order the tabs show them.
# "keywords" are looked for in the location_english column (lower case).
HALLS = [
    {"id": "fengyun", "name": "Fengyun", "name_zh": "風雲樓", "keywords": ["fengyun"]},
    {"id": "shuimu", "name": "Shuimu", "name_zh": "水木生活中心", "keywords": ["shuimu"]},
    {"id": "xcb", "name": "XCB", "name_zh": "小吃部", "keywords": ["xcb", "xiaochi", "snack bar"]},
]

# Average minutes to make one order, per vendor. Time real orders at peak hour and update
# these. Vendors not listed use DEFAULT_PREP_MIN.
DEFAULT_PREP_MIN = 3
PREP_MIN = {
    "MN Tea Time & Tea Lounge": 2,
    "Miss Charcoal Grill": 5,
    "Parson Pasta": 5,
}

# Opening hours per vendor, e.g. "10:30-14:00, 16:30-19:30". These win over the CSV's
# opening_hours column. A vendor with no hours anywhere is treated as open all day.
# Go and check the real hours (they differ per stall and change in the holidays).
OPENING_HOURS = {
}


def slug(text):
    """"Love Curry" -> "love-curry": a name that is safe to put in a web address."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def to_number(value):
    """"80" -> 80, "325.45" -> 325.45, "" or "n/a" -> None."""
    value = (value or "").strip()
    try:
        number = float(value)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def find_hall(location_english):
    """Which dining hall id a row belongs to, or None if no keyword matches."""
    location = (location_english or "").lower()
    for hall in HALLS:
        if any(keyword in location for keyword in hall["keywords"]):
            return hall["id"]
    return None


def read_menu_csv(lines):
    """Read one CSV file (any iterable of text lines) and return (vendors, skipped_rows).

    vendors is a list of dicts, each with an "items" list, ready for models.save_menu().
    """
    vendors = {}
    skipped = 0
    for row in csv.DictReader(lines):
        hall_id = find_hall(row.get("location_english"))
        name = (row.get("store_name_english") or "").strip()
        dish = (row.get("EnglishName") or row.get("dish_name") or "").strip()
        if hall_id is None or not name or not dish:
            skipped += 1
            continue

        key = (hall_id, name)
        hours = OPENING_HOURS.get(name, (row.get("opening_hours") or "").strip())
        try:
            parse_hours(hours)
        except ValueError as err:
            raise ValueError(f"{name}: {err}") from None
        if key in vendors and hours and not vendors[key]["hours"]:
            vendors[key]["hours"] = hours  # the hours only need to be on one row of the vendor
        if key not in vendors:
            vendors[key] = {
                "slug": f"{hall_id}-{slug(name)}",
                "hall": hall_id,
                "name": name,
                "name_zh": (row.get("store_name") or "").strip(),
                "cuisine": (row.get("cuisine") or "").strip(),
                "avg_prep_min": PREP_MIN.get(name, DEFAULT_PREP_MIN),
                "hours": hours,
                "items": [],
            }
        vendors[key]["items"].append({
            "name": dish,
            "name_zh": (row.get("ChineseName") or "").strip(),
            "price": to_number(row.get("price")),
            "calories": to_number(row.get("calories")),
            "category": (row.get("category") or "other").strip() or "other",
            "vegetarian": (row.get("is_vegetarian") or "").strip().upper() == "TRUE",
        })
    return list(vendors.values()), skipped


def read_all_csv(folder=DATA_DIR):
    """Read every .csv in the folder. Returns (vendors, skipped_rows)."""
    all_vendors, all_skipped = [], 0
    for path in sorted(Path(folder).glob("*.csv")):
        # utf-8-sig also handles the invisible marker Excel puts at the start of a CSV
        with open(path, encoding="utf-8-sig", newline="") as f:
            vendors, skipped = read_menu_csv(f)
        all_vendors += vendors
        all_skipped += skipped
    return all_vendors, all_skipped
