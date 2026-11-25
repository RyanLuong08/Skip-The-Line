"""Vendor PIN: only staff can open the vendor dashboard and the stats page (owner: B).

Students order without logging in. Vendors type a PIN once per browser; after that their
session cookie (signed with the secret key) remembers them.

Where the PIN comes from, in this order:
1. the VENDOR_PIN environment variable, if it is set, or
2. instance/vendor_pin, a random 6-digit PIN made on the first run (git ignores instance/).
   `python app.py` prints it, so the team can read it off the terminal.

choose_pin() and pin_matches() are plain Python with no Flask, so they are easy to test.
"""

import hmac
import os
import secrets
from functools import wraps
from urllib.parse import urlsplit

from flask import (Blueprint, current_app, jsonify, redirect, render_template, request,
                   session, url_for)

staff_auth = Blueprint("staff_auth", __name__)

PIN_FILE = "vendor_pin"
PIN_DIGITS = 6
MIN_PIN_LENGTH = 4
SESSION_KEY = "staff"


def new_pin():
    """A random 6-digit PIN, e.g. "048213"."""
    return f"{secrets.randbelow(10 ** PIN_DIGITS):0{PIN_DIGITS}d}"


def choose_pin(env_value, saved_value):
    """Return (pin, must_save). must_save is True when a new PIN was made."""
    for value in (env_value, saved_value):
        text = (value or "").strip()
        if len(text) >= MIN_PIN_LENGTH:
            return text, False
    return new_pin(), True


def pin_matches(given, real):
    """True if the typed PIN is right. compare_digest takes the same time whatever is typed,
    so nobody can guess the PIN by timing the answers."""
    if not isinstance(given, str) or not real:
        return False
    return hmac.compare_digest(given.strip().encode(), real.encode())


def safe_next(target):
    """Only send people back to a page on this site after login (never to another website)."""
    if not target:
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


def setup_pin(app, pin=None):
    """Set app.config["VENDOR_PIN"]. Tests pass a pin; otherwise use the env or the PIN file."""
    if pin is not None:
        app.config["VENDOR_PIN"] = pin
        return
    path = os.path.join(app.instance_path, PIN_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            saved = f.read()
    except FileNotFoundError:
        saved = None
    value, must_save = choose_pin(os.environ.get("VENDOR_PIN"), saved)
    if must_save:
        os.makedirs(app.instance_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(value)
    app.config["VENDOR_PIN"] = value


def is_staff():
    return session.get(SESSION_KEY) is True


def staff_required(view):
    """Put @staff_required under a route: pages send people to the PIN page, /api/... says 401."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if is_staff():
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify(error="Vendor PIN needed. Open /vendor and log in again."), 401
        return redirect(url_for("staff_auth.login", next=request.full_path.rstrip("?")))
    return wrapper


@staff_auth.route("/vendor/login", methods=["GET", "POST"])
def login():
    target = safe_next(request.values.get("next")) or url_for("vendor_api.vendor_page")
    if is_staff():
        return redirect(target)
    error = None
    if request.method == "POST":
        if pin_matches(request.form.get("pin"), current_app.config.get("VENDOR_PIN")):
            session[SESSION_KEY] = True
            return redirect(target)
        error = "Wrong PIN. Ask the team for the vendor PIN."
    return render_template("login.html", error=error, next=target), (401 if error else 200)


@staff_auth.route("/vendor/logout", methods=["POST"])
def logout():
    session.pop(SESSION_KEY, None)
    return redirect(url_for("home"))
