"""
Turn every CSV in data/raw/ into one file, data/menu.json, that the app reads.

Usage (run from the project folder):
    python scripts/build_menu.py

To add Shuimu or XCB: save the teammate's sheet as a CSV with the SAME columns
as Fengyun.csv, put it in data/raw/, and run this script again.
The dining hall is detected from the "location_english" column.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = ROOT / "data" / "menu.json"

# The three dining areas. "keywords" are matched against location_english.
HALLS = [
    {"id": "fengyun", "name": "Fengyun", "nameZh": "風雲樓", "keywords": ["fengyun"]},
    {"id": "shuimu", "name": "Shuimu", "nameZh": "水木生活中心", "keywords": ["shuimu"]},
    {"id": "xcb", "name": "XCB", "nameZh": "小吃部", "keywords": ["xcb", "xiaochi", "snack bar"]},
]

# Average minutes to prepare one order, per vendor. Change these once you have
# real timings from on-site observation. Vendors not listed use DEFAULT_PREP_MIN.
DEFAULT_PREP_MIN = 3
PREP_MIN = {
    "MN Tea Time & Tea Lounge": 2,
    "Miss Charcoal Grill": 5,
    "Parson Pasta": 5,
}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def to_number(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def find_hall(location_english):
    loc = (location_english or "").lower()
    for hall in HALLS:
        if any(k in loc for k in hall["keywords"]):
            return hall["id"]
    return None


def main():
    halls = {h["id"]: {**{k: v for k, v in h.items() if k != "keywords"}, "vendors": {}} for h in HALLS}
    skipped = 0

    for csv_path in sorted(RAW_DIR.glob("*.csv")):
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                hall_id = find_hall(row.get("location_english"))
                if hall_id is None:
                    skipped += 1
                    continue
                vendor_name = row["store_name_english"].strip()
                vendors = halls[hall_id]["vendors"]
                if vendor_name not in vendors:
                    vendors[vendor_name] = {
                        "id": f"{hall_id}-{slug(vendor_name)}",
                        "name": vendor_name,
                        "nameZh": row["store_name"].strip(),
                        "cuisine": row.get("cuisine", "").strip(),
                        "avgPrepMin": PREP_MIN.get(vendor_name, DEFAULT_PREP_MIN),
                        "items": [],
                    }
                vendors[vendor_name]["items"].append({
                    "id": f"{hall_id}-{row['id'].strip()}",
                    "name": (row.get("EnglishName") or row["dish_name"]).strip(),
                    "nameZh": (row.get("ChineseName") or "").strip(),
                    "price": to_number(row.get("price")),
                    "calories": to_number(row.get("calories")),
                    "category": (row.get("category") or "other").strip(),
                    "vegetarian": (row.get("is_vegetarian") or "").strip().upper() == "TRUE",
                })

    output = {"halls": []}
    for hall in halls.values():
        hall["vendors"] = sorted(hall["vendors"].values(), key=lambda v: v["name"])
        output["halls"].append(hall)
        items = sum(len(v["items"]) for v in hall["vendors"])
        print(f"{hall['name']:8} {len(hall['vendors']):3} vendors {items:4} items")

    OUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8")
    if skipped:
        print(f"Skipped {skipped} rows whose location_english matched no dining hall.")
    print(f"Wrote {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
