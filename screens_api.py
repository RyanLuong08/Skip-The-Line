"""Screens for the counter and the classroom (owner: B).

/board?hall=fengyun  A "Now serving" screen for a TV or laptop at the dining hall: every vendor's
                     ready ticket numbers in big type, and what is cooking. No PIN needed: it only
                     shows ticket numbers.
/qr                  This site's address as a big QR code, to put on the projector so the class can
                     scan it. Open /qr through the link people should use (the ngrok https:// link
                     for the demo); opened on the laptop itself it shows the laptop's Wi-Fi address.
"""

import socket

from flask import Blueprint, Response, jsonify, render_template, request

from menu_import import HALLS
from models import Order, Vendor, db
from queue_rules import COOKING, READY, WAITING, today

screens_api = Blueprint("screens_api", __name__)


@screens_api.route("/board")
def board_page():
    # The same address as the QR code in its corner, without "http://" and the last "/".
    address = site_address()[0].split("://", 1)[1].rstrip("/")
    return render_template("board.html", address=address)


@screens_api.route("/api/board")
def board_data():
    """Ticket numbers per vendor in one hall: ready (come and get it), cooking, waiting."""
    hall = request.args.get("hall", "fengyun")
    if hall not in {h["id"] for h in HALLS}:
        return jsonify(error="Unknown dining hall"), 404
    vendors = db.session.execute(
        db.select(Vendor).where(Vendor.hall == hall).order_by(Vendor.name)).scalars().all()
    orders = db.session.execute(
        db.select(Order).join(Vendor)
        .where(Vendor.hall == hall, Order.day == today(), Order.status.in_((WAITING, COOKING, READY)))
        .order_by(Order.ticket)
    ).scalars().all()
    rows = []
    for v in vendors:
        mine = [o for o in orders if o.vendor_id == v.id]
        rows.append({"slug": v.slug, "name": v.name, "name_zh": v.name_zh,
                     "ready": [o.ticket for o in mine if o.status == READY],
                     "cooking": [o.ticket for o in mine if o.status == COOKING],
                     "waiting": sum(1 for o in mine if o.status == WAITING)})
    # Vendors with something to show first, so a long list doesn't hide the busy ones.
    rows.sort(key=lambda r: (not (r["ready"] or r["cooking"] or r["waiting"]), r["name"]))
    name = next(h for h in HALLS if h["id"] == hall)
    return jsonify(hall={"id": hall, "name": name["name"], "name_zh": name["name_zh"]}, vendors=rows)


def lan_address():
    """This laptop's address on the Wi-Fi, e.g. 192.168.1.23 (None if it can't tell).
    Connecting a UDP socket sends nothing; it only makes the computer pick its network card."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def site_address():
    """The address phones should open: the one this page was opened with, except that
    localhost (useless on a phone) is swapped for the laptop's Wi-Fi address."""
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)  # ngrok says "https" here
    host = request.host
    name, _, port = host.partition(":")
    local = name in ("localhost", "127.0.0.1")
    if local:
        ip = lan_address()
        if ip:
            host = f"{ip}:{port}" if port else ip
    return f"{scheme}://{host}/", local


def qr_svg(text):
    """The QR code as an <svg> string, or None if the qrcode package isn't installed."""
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return None
    image = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    return image.to_string(encoding="unicode")


@screens_api.route("/qr.svg")
def qr_image():
    """The QR code picture (used by /qr and the corner of /board)."""
    svg = qr_svg(site_address()[0])
    if svg is None:
        return Response("qrcode is not installed", status=404, mimetype="text/plain")
    response = Response(svg, mimetype="image/svg+xml")
    response.headers["Cache-Control"] = "no-store"  # the address changes with every new ngrok link
    return response


@screens_api.route("/qr")
def qr_page():
    address, was_local = site_address()
    return render_template("qr.html", address=address, has_qr=qr_svg(address) is not None,
                           was_local=was_local, https=address.startswith("https://"))
