# Skip the Line 🍱

Order ahead at NTHU campus dining areas (Fengyun, Shuimu, XCB) and skip the peak-hour queue.
First Year Seminar group project.

**Live site:** https://ryanluong08.github.io/Skip-The-Line/ (after GitHub Pages is turned on)

## What it does

- **Student page** (`index.html`): pick a dining area and vendor, see the live queue and estimated wait,
  add dishes, choose a pickup time, and get a ticket number that updates as the order is cooked.
- **Vendor page** (`vendor.html`): incoming orders in three columns (New → Cooking → Ready),
  plus a "Now serving" number.

Wait estimate = orders ahead × the vendor's average minutes per order (`avgPrepMin` in `scripts/build_menu.py`).

## Run it on your computer

```bash
python -m http.server 8000
```
Then open http://localhost:8000. (Or use the VS Code **Live Server** extension.)
Opening `index.html` by double-clicking will not work, because browsers block loading `data/menu.json` from `file://`.

## Project structure

```
index.html, vendor.html   the two pages
css/style.css             all styling
js/config.js              settings: BACKEND ("local" or "firebase"), Firebase keys, peak hours
js/app.js                 student page logic
js/vendor.js              vendor page logic
js/store.js               saves/loads orders (picks local or Firebase)
js/util.js                shared helpers: wait estimate, time slots, menu loading
data/raw/*.csv            menu data collected by the team (one CSV per dining area)
data/menu.json            generated from the CSVs; this is what the app reads
scripts/build_menu.py     CSV -> menu.json
firestore.rules           database security rules (for the Firebase step)
docs/GUIDE.md             step-by-step setup and team workflow
```

## Update the menu

Put a CSV with the same columns as `data/raw/Fengyun.csv` in `data/raw/`, then run:
```bash
python scripts/build_menu.py
```

## Data status

| Dining area | Vendors | Dishes | Status |
|---|---|---|---|
| Fengyun 風雲樓 | 10 | 286 | Done (119 dishes still need prices) |
| Shuimu 水木 | – | – | Being collected |
| XCB 小吃部 | – | – | Being collected |
