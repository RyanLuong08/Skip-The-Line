"""Database tables (owner: B).

Flask-SQLAlchemy turns each class below into a table in a SQLite file
(instance/skipline.db). Every db.Column attribute becomes a column in that table.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from menu_import import read_all_csv
from payment_rules import COUNTER
from queue_rules import ACTIVE, WAITING, now

db = SQLAlchemy()


class Vendor(db.Model):
    """A food stall in one of the dining halls, e.g. Love Curry in Fengyun."""

    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)  # e.g. "fengyun-love-curry"
    hall = db.Column(db.String(20), nullable=False, index=True)  # "fengyun", "shuimu" or "xcb"
    name = db.Column(db.String(100), nullable=False)
    name_zh = db.Column(db.String(100), nullable=False, default="")
    cuisine = db.Column(db.String(50), nullable=False, default="")
    avg_prep_min = db.Column(db.Integer, nullable=False, default=3)  # minutes to make one order

    items = db.relationship("MenuItem", back_populates="vendor", order_by="MenuItem.id",
                            cascade="all, delete-orphan")

    def to_dict(self):
        return {"slug": self.slug, "hall": self.hall, "name": self.name, "name_zh": self.name_zh,
                "cuisine": self.cuisine, "avg_prep_min": self.avg_prep_min}


class MenuItem(db.Model):
    """One dish on a vendor's menu."""

    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    name_zh = db.Column(db.String(150), nullable=False, default="")
    price = db.Column(db.Integer, nullable=True)  # None: not collected yet, pay at the counter
    calories = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(30), nullable=False, default="other")
    vegetarian = db.Column(db.Boolean, nullable=False, default=False)

    vendor = db.relationship("Vendor", back_populates="items")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "name_zh": self.name_zh, "price": self.price,
                "calories": self.calories, "category": self.category, "vegetarian": self.vegetarian}


class Order(db.Model):
    """One student's order at one vendor. Its ticket number is what they show at the counter."""

    __tablename__ = "orders"
    # Two orders can never share a ticket number at the same vendor on the same day.
    __table_args__ = (db.UniqueConstraint("vendor_id", "day", "ticket"),)

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False, index=True)
    day = db.Column(db.String(10), nullable=False, index=True)  # "2026-11-19", Taiwan time
    ticket = db.Column(db.Integer, nullable=False)
    pickup = db.Column(db.String(5), nullable=False, default="ASAP")  # "ASAP" or "12:30"
    status = db.Column(db.String(10), nullable=False, default=WAITING)
    total = db.Column(db.Integer, nullable=False, default=0)  # dishes without a price count as 0
    payment = db.Column(db.String(10), nullable=False, default=COUNTER)  # "transfer" or "counter"
    transfer_ref = db.Column(db.String(5), nullable=False, default="")  # last 5 digits of the payer's account
    paid = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    vendor = db.relationship("Vendor")
    lines = db.relationship("OrderLine", back_populates="order", order_by="OrderLine.id",
                            cascade="all, delete-orphan")

    def to_dict(self, ahead=None):
        data = {
            "id": self.id, "ticket": self.ticket, "status": self.status, "pickup": self.pickup,
            "total": self.total, "created_at": self.created_at.strftime("%H:%M"),
            "payment": self.payment, "transfer_ref": self.transfer_ref, "paid": self.paid,
            "vendor": {"slug": self.vendor.slug, "name": self.vendor.name},
            "lines": [line.to_dict() for line in self.lines],
            "unpriced": any(line.price is None for line in self.lines),
        }
        if ahead is not None:
            data["ahead"] = ahead
        return data


class OrderLine(db.Model):
    """One dish in an order. The name and price are copied, so changing the menu later
    never changes an order that was already placed."""

    __tablename__ = "order_lines"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, nullable=True)  # no ForeignKey: menu items can be re-imported
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Integer, nullable=True)
    qty = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("Order", back_populates="lines")

    def to_dict(self):
        return {"name": self.name, "price": self.price, "qty": self.qty}


# ---------- Helpers that several blueprints use ----------

def active_order_ids(vendor_id, day):
    """Ids of the orders still being made at this vendor today, oldest first."""
    query = (db.select(Order.id)
             .where(Order.vendor_id == vendor_id, Order.day == day, Order.status.in_(ACTIVE))
             .order_by(Order.id))
    return db.session.execute(query).scalars().all()


def queue_lengths(day):
    """{vendor_id: number of orders still being made today} for every vendor with a queue."""
    query = (db.select(Order.vendor_id, func.count())
             .where(Order.day == day, Order.status.in_(ACTIVE))
             .group_by(Order.vendor_id))
    return dict(db.session.execute(query).all())


def save_menu(vendors):
    """Save vendors from menu_import.read_all_csv(). A vendor that already exists (same slug)
    keeps its id and orders, but its dishes are replaced by the ones in the CSV."""
    for data in vendors:
        vendor = db.session.execute(db.select(Vendor).filter_by(slug=data["slug"])).scalar_one_or_none()
        if vendor is None:
            vendor = Vendor(slug=data["slug"])
            db.session.add(vendor)
        for field in ("hall", "name", "name_zh", "cuisine", "avg_prep_min"):
            setattr(vendor, field, data[field])
        vendor.items = [MenuItem(**item) for item in data["items"]]
    db.session.commit()


def seed_menu_if_empty():
    """On the very first run, load data/*.csv so the app is never empty."""
    if db.session.execute(db.select(Vendor.id).limit(1)).first() is None:
        vendors, _ = read_all_csv()
        save_menu(vendors)
