# Skip the Line: step-by-step guide

For the two coders on the team. Follow the steps in order. Steps 1–6 take about an hour the first time.

**Project folder:** `D:\NTHU\First Year Seminar\First-Year-Seminar\Skip-The-Line`
**GitHub repo:** https://github.com/RyanLuong08/Skip-The-Line

---

## How the app works (read this first)

```
 Student phone                         Vendor tablet
 index.html                            vendor.html
   pick vendor, order, get #12           see #12 → Start cooking → Mark ready
          \                              /
           \                            /
            js/store.js  (one place that saves and loads orders)
              ├── store-local.js     → this browser only (for building and demos)
              └── store-firebase.js  → cloud database, shared by every device (Step 10)

 data/raw/Fengyun.csv ──(scripts/build_menu.py)──► data/menu.json ──► both pages read the menu
```

It is plain HTML, CSS and JavaScript: no frameworks and no build step. That means GitHub Pages can host it for free,
and you can read every file without learning a framework first.

---

## Step 1. Install the tools (both coders)

1. **Git**: https://git-scm.com/download/win. Accept the defaults. Keep "Git Credential Manager" ticked, since it lets you sign in to GitHub through the browser.
2. **VS Code**: https://code.visualstudio.com. Then open Extensions (Ctrl+Shift+X) and install **Live Server** (by Ritwick Dey).
3. **Python 3**: https://www.python.org/downloads/. On the first installer screen, tick **"Add python.exe to PATH"**.
4. **GitHub account**: https://github.com/signup (use your school email if you want GitHub Education perks later).

Check that everything installed. Open **PowerShell** and run:
```powershell
git --version
python --version
```
Both should print a version number. If `python` opens the Microsoft Store instead, reinstall Python with the PATH box ticked.

## Step 2. Tell Git who you are (both coders, once per computer)

```powershell
git config --global user.name "Your Name"
git config --global user.email "the-email-on-your-github-account@example.com"
git config --global init.defaultBranch main
```

## Step 3. Get access to the repo

The repo `Skip-The-Line` is under the GitHub account **RyanLuong08**.

- **If that's you:** go to the repo on GitHub → **Settings → Collaborators → Add people**, and invite your teammate's GitHub username. They accept the invite from their email or https://github.com/notifications.
- **If that's your teammate:** ask them to invite you as above.
- **If the repo doesn't exist on GitHub yet:** sign in as RyanLuong08 → **+ (top right) → New repository** → name it `Skip-The-Line`, set it to **Public**, and **don't** tick "Add a README" (the project already has one). Click **Create repository**.

## Step 4. Open and run the project

1. Open VS Code → **File → Open Folder** → choose `D:\NTHU\First Year Seminar\First-Year-Seminar\Skip-The-Line`.
2. Right-click `index.html` → **Open with Live Server**. The browser opens at something like `http://127.0.0.1:5500/index.html`.
   - No Live Server? In VS Code's terminal (Ctrl+`) run `python -m http.server 8000` and open http://localhost:8000.
   - Don't double-click `index.html`. Browsers block the menu file when a page is opened that way, and you'll see an empty page.
3. Try it:
   - Click **Love Curry**, add two dishes, click **Place order**. A ticket **#1** appears under "My tickets".
   - Click **Vendor view →** (or open `vendor.html` in a second tab), choose *Fengyun · Love Curry*, and click **Start cooking**, then **Mark ready**.
   - Switch back to the student tab. The ticket now says **Ready for pickup**.

While `BACKEND = "local"`, orders live only in that one browser. To clear them: press F12 → **Application** tab → **Local Storage** → right-click → **Clear**.

## Step 5. Learn your way around the code (30 minutes, worth it)

Read the files in this order. Each one is short and commented.

| File | What to look for |
|---|---|
| `js/config.js` | The settings you'll change: backend, Firebase keys, peak hours, pickup slot spacing |
| `js/util.js` | `estimateWaitMin()` is the wait-time formula; `pickupSlots()` builds the time list |
| `js/store.js` | The 3 functions everything else uses: `subscribeOrders`, `placeOrder`, `setStatus` |
| `js/app.js` | Student page. Pattern: **state → render() → events change state → render() again** |
| `js/vendor.js` | Vendor page, same pattern |
| `scripts/build_menu.py` | How CSV rows become `data/menu.json`; `PREP_MIN` sets each vendor's minutes per order |

Practice change: in `config.js`, change `SLOT_STEP_MIN` to `15`, save, and watch the pickup times change in the browser.

## Step 6. First commit and push to GitHub (whoever owns the repo)

The folder is already a Git repo connected to GitHub, so you only need to commit and push. In VS Code's terminal:

```powershell
cd "D:\NTHU\First Year Seminar\First-Year-Seminar\Skip-The-Line"
git status                      # lists the new files (red = not yet staged)
git add .
git commit -m "Starter app: student ordering page, vendor dashboard, Fengyun menu"
git branch -M main
git push -u origin main
```

The first push opens a browser window to sign in to GitHub. Refresh the repo page on GitHub and your files are there.

> **If you see** `fatal: not a git repository`: run `git init` then `git remote add origin https://github.com/RyanLuong08/Skip-The-Line.git` and try again.
> **If you see** `rejected ... fetch first`: the GitHub repo already has a commit (e.g. a README made on the website). Run `git pull origin main --allow-unrelated-histories`, then push again.

## Step 7. Your teammate gets a copy

On the teammate's computer (after accepting the invite):
```powershell
cd D:\           # or anywhere they like
git clone https://github.com/RyanLuong08/Skip-The-Line.git
cd Skip-The-Line
code .           # opens it in VS Code
```

## Step 8. Daily team workflow (both coders)

Use one **branch per task** so you never overwrite each other.

```powershell
git checkout main
git pull                                  # 1. get the latest version
git checkout -b vendor-sound-alert        # 2. new branch named after the task
# ... edit, test in the browser ...
git add .
git commit -m "Vendor page: play a sound when a new order arrives"
git push -u origin vendor-sound-alert     # 3. upload the branch
```

Then on GitHub: click **Compare & pull request** → **Create pull request**. The other coder reads it, clicks **Merge**, and you both `git checkout main` and `git pull`.

**Splitting the work** so you rarely edit the same file:

| Coder A | Coder B |
|---|---|
| Student page (`index.html`, `js/app.js`) | Vendor page (`vendor.html`, `js/vendor.js`) |
| Wait-time formula (`js/util.js`) | Menu data and script (`data/`, `scripts/`) |
| Firebase setup (Step 10) | GitHub Pages and testing on phones (Step 9) |

**Merge conflict?** VS Code highlights the clashing lines with *Accept Current / Accept Incoming / Accept Both*. Pick the right one, save, then `git add .` and `git commit`.

## Step 9. Publish it on GitHub Pages (free website)

1. On GitHub: repo → **Settings → Pages**.
2. **Source:** *Deploy from a branch*. **Branch:** `main`, folder `/ (root)` → **Save**.
3. Wait 1–2 minutes and refresh. The address appears at the top: **https://ryanluong08.github.io/Skip-The-Line/**
4. Every push to `main` updates the site automatically within a minute or two.

Put this link on slide 7 of the presentation. The repo needs to be **Public** for free Pages.

## Step 10. Make orders shared across phones (Firebase)

With `BACKEND = "local"`, a student's phone and the vendor's tablet can't see each other's orders. Firebase's free plan fixes that.

1. Go to https://console.firebase.google.com → **Create a project** → name it `skip-the-line` → Google Analytics can be off → **Create**.
2. Left menu **Build → Firestore Database → Create database**. Location: **asia-east1 (Taiwan)**. Start in **production mode**.
3. Open the **Rules** tab, replace everything with the contents of `firestore.rules` from this project, and click **Publish**.
4. Click the **gear icon → Project settings → General**. Under "Your apps", click the **web icon `</>`**, name it `web`, and **don't** tick Firebase Hosting → **Register app**.
5. Firebase shows a `firebaseConfig = { ... }` block. Copy the values into `js/config.js` → `firebaseConfig`.
6. In `js/config.js` set `export const BACKEND = "firebase";`
7. Test: open the site on your phone and on your laptop. Order on the phone and the order appears on the laptop's vendor page within a second.
8. Commit and push. The Firebase web config is safe to publish, because the security rules (step 3) are what protect the database.

If orders don't appear, press F12 → **Console**. `Missing or insufficient permissions` means the rules from step 3 weren't published.

## Step 11. Add Shuimu and XCB when the data arrives

1. Teammates fill a sheet with **exactly the same columns** as `data/raw/Fengyun.csv`. Copy the header row so the columns match.
   In `location_english`, write `Shuimu ...` or `XCB ...` so the script knows which dining area each row is in.
2. Export it as CSV: Google Sheets → **File → Download → .csv**. In Excel, use **Save As → CSV UTF-8** (plain "CSV" garbles Chinese text).
3. Save it as `data/raw/Shuimu.csv` (or `XCB.csv`) and run:
   ```powershell
   python scripts/build_menu.py
   ```
   It prints how many vendors and dishes each area has. Refresh the browser and the new tab is filled in.
4. Commit both the CSV and `data/menu.json`, then push.

Fengyun still has **119 dishes without prices** (mostly Parson Pasta, Manikaba and Moni Burritos). The app shows "Ask at counter" for those until the CSV is filled in.

## Step 12. Make the wait estimate real (helps the presentation)

The estimate is `orders ahead × avgPrepMin`, and every vendor currently uses a guess of 2–5 minutes.
During a peak hour, time 10 orders at each vendor (from paying to receiving food) and put the averages into `PREP_MIN`
in `scripts/build_menu.py`, then re-run it. This also gives you real numbers for the "Why" and "Solution" slides.

---

## Ideas for after the basics work

- [ ] Sound or vibration on the vendor page when a new order arrives
- [ ] A "Now serving" screen for a TV at the counter (`board.html`)
- [ ] Hide vendors that are closed right now (add opening hours to the data)
- [ ] Vendor sign-in (Firebase Authentication) so only vendors can change order status
- [ ] No-show rule: decide on 2 or 3 strikes. The demo and the slides disagree, so the team should pick one.
- [ ] 中文/English language switch
- [ ] Live crowd chart per hour, built from past orders

## Troubleshooting

| Problem | Fix |
|---|---|
| Blank page, Console says `Failed to fetch data/menu.json` | You opened the file directly. Use Live Server or `python -m http.server` (Step 4). |
| Changes don't show up | Hard refresh: **Ctrl+F5**. GitHub Pages can take ~1 min after a push. |
| `git push` asks for a password | Passwords don't work anymore. Close the prompt and let the browser sign-in window appear, or reinstall Git with Credential Manager. |
| `Permission denied` on push | You haven't accepted the collaborator invite (Step 3). |
| Chinese text shows as `ç¾...` | Save the CSV as **CSV UTF-8**. |
| Firebase `Missing or insufficient permissions` | Publish `firestore.rules` (Step 10.3). |
