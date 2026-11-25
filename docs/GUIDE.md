# Skip the Line: step-by-step guide

For the two coders on the team (called **A** and **B** below, like in our I2P project).
It is set up the same way as the I2P geocaching project: Flask + Flask-SQLAlchemy + SQLite, one Blueprint per `*_api.py` file,
plain-Python rule files that are easy to test, Jinja templates, and `unittest` tests.

**Project folder:** `D:\NTHU\First Year Seminar\First-Year-Seminar\Skip-The-Line`
**GitHub repo:** https://github.com/RyanLuong08/Skip-The-Line

---

## How the app works

```
 Student phone (/)                                   Vendor tablet (/vendor)
   pick vendor, add dishes, Place order                sees #12 → Start cooking → Mark ready
          │  POST /api/orders                                 │  POST /api/orders/12/status
          │  GET  /api/my-orders  (every 4 s)                 │  GET  /api/vendors/<slug>/orders (every 3 s)
          ▼                                                   ▼
   order_api.py ──── queue_rules.py / order_input.py ──── vendor_api.py      menu_api.py
          └───────────────────── models.py (SQLAlchemy) ─────────────────────────┘
                                     instance/skipline.db (SQLite)
                                            ▲
                    data/Fengyun.csv ── menu_import.py (loaded on the first run)
```

The pages never decide anything important. They ask Python, and Python checks the prices, hands out ticket numbers and
refuses impossible moves (like *ready → cooking*). One server holds one database, so every phone sees the same queue.

---

## Step 1. Install the tools (both coders)

You already have these from I2P. If not:
1. **Python 3.12 or newer**: https://www.python.org/downloads/ (tick **"Add python.exe to PATH"**).
2. **Git**: https://git-scm.com/download/win (keep the defaults).
3. **VS Code** with the **Python** extension (by Microsoft).

## Step 2. Get the code

**Coder A (Ryan), who already has the folder:** first merge the pull request on GitHub (I'll send the link), then:
```powershell
cd "D:\NTHU\First Year Seminar\First-Year-Seminar\Skip-The-Line"
git checkout main
git pull
```
`git pull` deletes the old JavaScript files and brings in the Python ones, so the folder is cleaned up for you.

**Coder B:** accept the collaborator invite (GitHub email or https://github.com/notifications), then:
```powershell
cd D:\NTHU
git clone https://github.com/RyanLuong08/Skip-The-Line.git
cd Skip-The-Line
```

## Step 3. Make the virtual environment (once per computer)

Same as I2P: the packages live in a `venv` folder inside the project (git ignores it).
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Your prompt now starts with `(venv)`. **Run `.\venv\Scripts\Activate.ps1` every time you open a new terminal.**

> PowerShell says *"running scripts is disabled"*? Run this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
>
> In VS Code: Ctrl+Shift+P → **Python: Select Interpreter** → pick the one in `.\venv`. New terminals then activate it for you.

## Step 4. Run it

```powershell
python app.py
```
- Student page: http://localhost:5000
- Vendor page: http://localhost:5000/vendor (asks for the **vendor PIN**, see Step 10e)
- Stats page: http://localhost:5000/stats (same PIN)

The first run creates `instance/skipline.db` and loads the menus from `data/` (Fengyun and XCB). It also prints
`Vendor PIN: 123456` in the terminal.

Try it: order two dishes at **Love Curry**, open `/vendor` in another tab, type the PIN, choose *fengyun · Love Curry*,
and click **Start cooking** then **Mark ready**. Within 4 seconds the student tab says **Ready for pickup**.

Stop the server with **Ctrl+C**.
To wipe all orders, stop the server, delete `instance\skipline.db`, and start it again.
To see the error details while coding, run `$env:FLASK_DEBUG = "1"; python app.py`.

## Step 5. Run the tests

```powershell
python -m unittest
```
You should see `Ran 110 tests ... OK`. **Run them before every push.** If you change a rule, change or add its test too.
Run one file with `python -m unittest tests.test_queue_rules`.

## Step 6. Learn your way around (30 minutes, worth it)

Read in this order. Each file starts with a comment saying what it does.

| Read | Look for |
| --- | --- |
| `queue_rules.py` | `estimate_wait_min`, `pickup_slots`, `ALLOWED_MOVES`, `PEAK_HOURS` |
| `order_input.py` | How every value from the browser is checked before it's used |
| `models.py` | The four tables and how `Order` keeps its own copy of each dish (`OrderLine`) |
| `order_api.py` | `_create_order`: how ticket numbers are handed out safely |
| `menu_api.py`, `vendor_api.py` | Small Blueprints, same pattern as `coin_api.py` in I2P |
| `templates/index.html` | The inline script: fetch `/api/...`, then draw with `el(...)` |
| `tests/helpers.py` | The tiny test menu every API test starts with |

Practice change: in `queue_rules.py` set `SLOT_STEP_MIN = 15`, run the tests (one will fail, so fix its expected times),
then restart the app and look at the pickup list.

## Step 7. Daily team workflow

One branch per task, then a pull request, just like I2P:
```powershell
git checkout main
git pull
git checkout -b vendor-sound-alert
# ... edit, run the app, run the tests ...
git add .
git commit -m "Vendor page: beep when a new order arrives"
git push -u origin vendor-sound-alert
```
On GitHub: **Compare & pull request** → **Create pull request**. The other coder reviews and clicks **Merge**.
Afterwards both run `git checkout main` and `git pull`.

The **Owner** column in the README says who usually edits which file, so you rarely touch the same file at once.

## Step 8. Try it on real phones

The server already listens on the whole network (`host="0.0.0.0"`).
1. Run `ipconfig` and find your laptop's **IPv4 Address**, e.g. `192.168.1.23`.
2. On a phone on the **same Wi-Fi**, open `http://192.168.1.23:5000`.
3. If Windows asks whether to allow Python through the firewall, click **Allow** (Private networks).

Campus Wi-Fi often blocks phones from reaching laptops. If the page doesn't load, turn on your phone's **hotspot** and
connect the laptop and the other phones to it. Or use **ngrok**, as in I2P: `ngrok http 5000` gives you a public link.

For the demo: one laptop runs the server and shows `/vendor`, and classmates order from their phones.

## Step 9. Add Shuimu and XCB when the data arrives

1. The sheet must have **exactly the same columns** as `data/Fengyun.csv` (copy its header row).
   Put `Shuimu ...` or `XCB ...` in the `location_english` column.
2. Export it as **CSV UTF-8**: in Google Sheets, File → Download → .csv; in Excel, Save As → *CSV UTF-8*.
3. Save it as `data/Shuimu.csv` or `data/XCB.csv`, then run:
   ```powershell
   python import_menu.py
   ```
   It prints how many vendors and dishes each hall has. Existing orders are kept.
4. Commit the CSV and push.

Fengyun still has **119 dishes without a price** (mostly Parson Pasta, Manikaba, Moni Burritos). The app shows
*Ask at counter* for those. Fill the prices in the CSV and run `python import_menu.py` again.

## Step 10. Make the wait estimate real

The estimate is *orders being made × `avg_prep_min`*, and each vendor's minutes are a guess (`PREP_MIN` in
`menu_import.py`). At peak hour, time about 10 orders per vendor (from paying to getting the food), put the averages in
`PREP_MIN`, and run `python import_menu.py`. Those timings are also good evidence for the presentation.

## Step 10b. Payment (transfer or pay at pickup)

The rules are in `payment_rules.py`: pay at pickup only when the total is **under** `COUNTER_LIMIT` (NT$200),
otherwise bank transfer. For a transfer the student types the last 5 digits of their account (後五碼); the vendor
finds the payment in their bank app, presses **Confirm paid**, and only then can press **Start cooking**.

Transfer stays switched off until there is a bank account to send money to. The account numbers **don't go in the
code** (the repo is public). Put them in `instance\bank_accounts.json`, which git never uploads:
```json
{
  "default": {"bank": "822 中國信託 CTBC", "account": "your real account number", "holder": "Your Name"},
  "vendors": {}
}
```
`default` is used by every vendor; a vendor slug under `vendors` (e.g. `"xcb-bistro": {...}`) gets its own account.
Restart the server after changing it. Never use a made-up account number. For the demo, use one teammate's real
account. Each laptop that runs the server needs its own copy of this file.

The payment, opening hours and push notifications added new columns and a table. After you `git pull` these changes,
**stop the server, delete `instance\skipline.db`, and start again** (otherwise you get `no such column: ...`).
Also run `python -m pip install -r requirements.txt` again (for `pywebpush`).

## Step 10c. Opening hours

Write each vendor's hours like `10:30-14:00, 16:30-19:30`, either in a new `opening_hours` column of the CSV (one row
per vendor is enough) or in `OPENING_HOURS` in `menu_import.py` (that one wins). Then run `python import_menu.py`.
A vendor without hours is treated as **open all day**, so go and check the real hours at each stall.
Closed vendors are greyed out, `ASAP` is only offered while a vendor is open, and Python refuses orders for a time
when the vendor is closed.

## Step 10d. "Your food is ready" on the phone

- **Page open:** the phone vibrates (no sound) and the tab title becomes `✅ #12 READY`. Vibration works on Android;
  iPhones don't let web pages vibrate.
- **Page closed or screen off:** the student taps **🔔 Notify me when my food is ready** under *My tickets*. When the
  vendor presses *Mark ready*, `push_api.py` sends a push notification that vibrates the phone.
  - Browsers only allow this on **https://** pages (or `localhost`). `http://192.168.x.x:5000` is not enough, so for
    the demo use **ngrok** (`ngrok http 5000`) and give classmates the https link.
  - **iPhone** (iOS 16.4 or newer): open the https link in Safari → Share → **Add to Home Screen**, then open Skip
    the Line from the home screen and tap *Notify me*.
  - The laptop running the server needs internet: the message goes through Google/Apple/Mozilla's push service.
  - The server's key is made on the first run and kept in `instance\vapid_private.pem`. If you delete it, every
    student has to tap *Notify me* again.

## Step 10e. Vendor PIN and the stats page

`/vendor` and `/stats` need a PIN, so a classmate who finds the link can't mark orders ready or see transfer digits.
Students never need it: ordering, *My tickets* and cancelling their own order work without it.

- The first `python app.py` makes a random 6-digit PIN, saves it in `instance\vendor_pin` and prints it.
  To choose your own, edit that file (4+ characters) or start with `$env:VENDOR_PIN = "246810"; python app.py`.
- Each vendor browser types it once; **Log out** is in the top bar.
- On the dashboard, press **🔕 Sound off** once to turn the sound on (browsers only allow sound after a click). Then a
  new order rings, its card is outlined in green, and the tab title shows `(1) New order`.

`/stats` shows one day at a time: orders per hour, the average minutes from ordering to *Mark ready*, order value,
cancellations, and per vendor the real cooking time (*Start cooking* → *Mark ready*). After a vendor has 3 or more
cooked orders it shows a **measured** minutes-per-order next to the one the wait estimate uses: copy it into
`PREP_MIN` in `menu_import.py` and run `python import_menu.py` (that's Step 10, done for you).
These numbers (busiest hour, minutes saved) are good evidence for the presentation.

This change added two columns (`cooking_at`, `ready_at`), so after pulling it: stop the server, delete
`instance\skipline.db`, start again.

## Step 10f. Sold out, pause, no-shows, board, QR, search, 中文

**On the vendor dashboard** (all reset by themselves the next morning):
- **⏸ Pause app orders**: for when the stall is swamped. Students see *Not taking app orders right now. Order at
  the counter.* Press it again to resume.
- **Menu: mark dishes sold out** (at the bottom): tick a dish. Students see it greyed out with *Sold out*, and
  Python refuses orders for it.
- **No-show**: on a *Ready* card, once the food has waited 15 minutes. Each no-show counts against that student's
  browser; after **3** in 30 days they can't choose *Pay at pickup* any more and must transfer first.
  The numbers are in `noshow_rules.py` (`NO_SHOW_LIMIT`, `NO_SHOW_AFTER_MIN`). **Agree on 2 or 3 as a team and make
  the slides match.** Limitation: with no student login, clearing the browser's cookies resets the count.

**Screens:**
- `/board?hall=fengyun`: a *Now serving* screen for a TV or a second laptop at the counter. Big ready numbers per
  vendor, refreshes every 5 seconds, with a QR code in the corner. No PIN needed (it only shows ticket numbers).
- `/qr`: the site's address as a big QR code for the projector. **Open it through the ngrok link** so the QR is the
  https link. Opened on the laptop itself, it shows the laptop's Wi-Fi address instead.
  Needs the `qrcode` package (`python -m pip install -r requirements.txt`).

**For students:**
- The search box above the vendors searches **every dish in every hall**, in English or Chinese, plus *Vegetarian*
  and *Under NT$100* filters. Pressing **+** on a result opens that vendor with the dish in the cart.
- **Order again** shows their last few orders (the browser remembers them for 60 days).
- **中文 / EN** in the top bar. The page starts in the phone's language. Every word is in `static/js/i18n.js`: to add a
  sentence, add the same key to both the `en` and `zh` lists (a test checks they match). Error messages that come
  from Python are still English only.

New columns again (`paused_day`, `sold_out_day`, `device`, `name_zh` on order lines): after pulling, delete
`instance\skipline.db` and start again.

## Step 11. Putting it online (optional)

GitHub only stores the code. **GitHub Pages can't run Python**, so if you turned Pages on for the old version, turn it
off (Settings → Pages → Unpublish). For a link that works without your laptop, a free Python host such as
**PythonAnywhere** or **Render** can run a Flask app from this repo. For the class demo, Step 8 is enough.

---

## Ideas for after the basics work

- [x] Vendor PIN, so only the stall can change its orders (Step 10e)
- [x] Beep on the vendor page when a new order arrives (Step 10e)
- [x] A "Now serving" screen for a TV at each counter (`/board`, Step 10f)
- [x] Opening hours, so closed vendors are greyed out (Step 10c)
- [x] No-show rule (Step 10f): **still decide 2 or 3 as a team** and set `NO_SHOW_LIMIT`
- [x] Sold out, pause, search all vendors, order again, QR page, 中文 / English (Step 10f)
- [ ] Student login with the student ID (makes the no-show rule impossible to dodge)
- [x] Orders-per-hour chart and real cooking times (`/stats`, Step 10e)
- [ ] Shuimu menu
- [ ] 中文 / English switch

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'flask'` | The venv isn't active: `.\venv\Scripts\Activate.ps1` |
| `pip.exe ... blocked by an Application Control policy` | Windows blocks the small `pip.exe` in each new venv. Always use `python -m pip ...` instead |
| `running scripts is disabled on this system` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (Step 3) |
| `Address already in use` / port 5000 busy | Another `python app.py` is still running. Close that terminal or press Ctrl+C in it |
| Menu is empty | Check `data/Fengyun.csv` exists, then delete `instance\skipline.db` and restart |
| Changed `models.py` and now get `no such column` | `db.create_all()` never changes old tables. Delete `instance\skipline.db` and restart |
| Chinese text shows as `ç¾...` | Save the CSV as **CSV UTF-8** |
| Phone can't open the page | Same Wi-Fi? Firewall allowed? Try a phone hotspot (Step 8) |
| No *Notify me* button | `python -m pip install -r requirements.txt` (pywebpush), then restart. On the phone, use the https:// (ngrok) link |
| Vendor page keeps asking for the PIN | The PIN is in `instance\vendor_pin` (also printed when the server starts) |
| Transfer is greyed out for every vendor | No `instance\bank_accounts.json` yet, or it has no `"default"` (Step 10b) |
| `/qr` says it needs the qrcode package | `python -m pip install -r requirements.txt`, then restart |
| QR code shows a `192.168...` address, not https | Open `/qr` through the ngrok https link instead of on localhost |
| Students say a dish is sold out but it isn't | The vendor ticked it under *Menu: mark dishes sold out*; untick it |
| `git push` rejected | `git pull` first, fix any conflicts, run the tests, push again |
