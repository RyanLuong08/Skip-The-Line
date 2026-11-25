"""Skip the Line: order ahead at NTHU dining halls. Run it with:  python app.py

Then open http://localhost:5000 (student page) and http://localhost:5000/vendor (vendor page,
needs the vendor PIN that this prints when it starts).
"""

import json
import os

from flask import Flask, render_template, send_from_directory

from menu_api import menu_api
from models import db, seed_menu_if_empty
from order_api import order_api
from payment_rules import parse_bank_accounts, use_bank_accounts
from push_api import push_api, setup_push
from secret_key import KEY_FILE, choose_secret_key, new_key
from staff_auth import setup_pin, staff_auth
from stats_api import stats_api
from vendor_api import vendor_api


def _secret_key(app, database_uri):
    """SECRET_KEY from the environment, or a random one kept in instance/secret_key."""
    if database_uri.startswith("sqlite:///:memory:"):
        return new_key()  # tests: a throwaway key, and no file written
    path = os.path.join(app.instance_path, KEY_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            saved = f.read()
    except FileNotFoundError:
        saved = None
    key, must_save = choose_secret_key(os.environ.get("SECRET_KEY"), saved)
    if must_save:
        os.makedirs(app.instance_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(key)
    return key


BANK_FILE = "bank_accounts.json"


def _load_bank_accounts(app):
    """Switch on bank transfers if instance/bank_accounts.json exists (see payment_rules.py)."""
    path = os.path.join(app.instance_path, BANK_FILE)
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        default, vendors = parse_bank_accounts(json.load(f))
    use_bank_accounts(default, vendors)


def create_app(database_uri="sqlite:///skipline.db", load_menu=True, vendor_pin=None):
    """Build the Flask app.

    The default database is a file in the "instance" folder. Tests pass
    "sqlite:///:memory:" so they get a fresh, throwaway database, and load_menu=False
    so they can add their own small menu, and a vendor_pin so they know the PIN.
    """
    app = Flask(__name__)
    app.register_blueprint(menu_api)
    app.register_blueprint(order_api)
    app.register_blueprint(vendor_api)
    app.register_blueprint(push_api)
    app.register_blueprint(staff_auth)
    app.register_blueprint(stats_api)
    app.config["SECRET_KEY"] = _secret_key(app, database_uri)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.json.ensure_ascii = False  # send Chinese dish names as they are, not as \u codes
    db.init_app(app)
    testing = database_uri.startswith("sqlite:///:memory:")
    setup_pin(app, vendor_pin if vendor_pin is not None else ("1234" if testing else None))
    if not testing:
        _load_bank_accounts(app)
    # Push notifications: off in tests (no key file is written), on if pywebpush is installed.
    setup_push(app, enabled=not database_uri.startswith("sqlite:///:memory:"))

    # Create the tables (if missing) and load the menu from data/ on the first run.
    with app.app_context():
        db.create_all()
        if load_menu:
            seed_menu_if_empty()

    @app.route("/")
    def home():
        """The student page."""
        return render_template("index.html")

    @app.route("/sw.js")
    def service_worker():
        """The service worker that shows push notifications. It has to be served from "/"
        (not /static/) so that it may work for the whole site."""
        response = send_from_directory(app.static_folder, "sw.js", mimetype="text/javascript")
        response.headers["Cache-Control"] = "no-cache"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    # Debug mode lets anyone who can reach the page run code on this computer, and
    # host 0.0.0.0 lets the whole Wi-Fi reach it. So debug is OFF unless you ask:
    #   $env:FLASK_DEBUG = "1"; python app.py
    debug = os.environ.get("FLASK_DEBUG") == "1"
    print(f"\n  Vendor PIN: {app.config['VENDOR_PIN']}   (kept in instance/vendor_pin)\n")
    app.run(host="0.0.0.0", port=5000, debug=debug)
