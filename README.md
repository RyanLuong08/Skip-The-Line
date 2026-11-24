# 🍱 Skip the Line

**Order ahead. Skip the queue. Eat on time.**

Skip the Line is a web app built with Python and Flask that lets NTHU students order ahead at the campus
dining halls (Fengyun, Shuimu, XCB) so they don't waste their lunch break standing in a peak-hour queue.
First Year Seminar group project.

---

## Features

| Feature | Description |
| --- | --- |
| **Dining halls and vendors** | Tabs for Fengyun, Shuimu and XCB. Each vendor shows its live queue and estimated wait. |
| **Menu** | Every dish with its Chinese name, price and calories, a search box and category filters. |
| **Order ahead** | Add dishes, choose *ASAP* or a pickup time, and get a ticket number. Python looks up the prices, so they can't be faked. |
| **My tickets** | Your tickets update by themselves: *In queue (2 ahead) → Cooking → Ready for pickup*. |
| **Vendor dashboard** | `/vendor`: orders in three columns (New → Cooking → Ready) and a big "Now serving" number. |
| **Wait estimate** | Orders still being made × the vendor's average minutes per order. |

## Run it

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000 for students and http://localhost:5000/vendor for vendors.
The first run creates `instance/skipline.db` and loads the menu from `data/`.

Run the tests with `python -m unittest`.

The full step-by-step setup and team workflow is in **[docs/GUIDE.md](docs/GUIDE.md)**.

## Project structure

| File | What it does | Owner |
| --- | --- | --- |
| `app.py` | Builds the Flask app, registers the blueprints, serves the student page | A |
| `queue_rules.py` | Plain Python: tickets, wait estimate, pickup times, allowed status changes | A |
| `order_input.py` | Plain Python: checks what the browser sends when ordering | A |
| `order_api.py` | `POST /api/orders`, `GET /api/my-orders` | A |
| `templates/index.html` | The student page | A |
| `models.py` | Database tables: Vendor, MenuItem, Order, OrderLine | B |
| `menu_import.py` | Plain Python: reads the menu CSV files | B |
| `import_menu.py` | `python import_menu.py` reloads the menu from `data/` | B |
| `menu_api.py` | `GET /api/halls`, `/api/vendors?hall=`, `/api/vendors/<slug>/menu`, `/api/now` | B |
| `vendor_api.py` | The vendor dashboard and `POST /api/orders/<id>/status` | B |
| `templates/vendor.html` | The vendor page | B |
| `secret_key.py` | Signs the session cookie that remembers "my tickets" | B |
| `tests/` | `unittest` tests for all of the above | both |

## Menu data

| Dining hall | Vendors | Dishes | Status |
| --- | --- | --- | --- |
| Fengyun 風雲樓 | 10 | 286 | Done (119 dishes still need prices) |
| Shuimu 水木 | – | – | Being collected |
| XCB 小吃部 | 6 | 162 | Done (all priced; calories are estimates; Chinese names still missing) |

To add a hall: save its sheet as a CSV with the same columns as `data/Fengyun.csv`, put it in `data/`,
and run `python import_menu.py`.
