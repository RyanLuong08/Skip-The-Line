"""Load (or reload) the menu from every CSV in data/ into the database.

    python import_menu.py

Run it after you add Shuimu.csv / XCB.csv or fix prices. Safe to run more than once:
vendors keep their orders, and their dishes are replaced by what the CSV says.
"""

from app import create_app
from menu_import import HALLS, read_all_csv
from models import save_menu

if __name__ == "__main__":
    app = create_app(load_menu=False)
    vendors, skipped = read_all_csv()
    with app.app_context():
        save_menu(vendors)
    for hall in HALLS:
        mine = [v for v in vendors if v["hall"] == hall["id"]]
        dishes = sum(len(v["items"]) for v in mine)
        print(f"{hall['name']:8} {len(mine):3} vendors {dishes:4} dishes")
    if skipped:
        print(f"Skipped {skipped} rows (no matching dining hall, vendor name or dish name).")
