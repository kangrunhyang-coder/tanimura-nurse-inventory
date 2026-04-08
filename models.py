from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AppSetting(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.String(500), nullable=False, default="")


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BoardMessage(db.Model):
    __tablename__ = "board_messages"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Area(db.Model):
    __tablename__ = "areas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, default=0)


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    formal_name = db.Column(db.String(300), default="")
    category = db.Column(db.String(100), nullable=False)
    par_level = db.Column(db.Integer, nullable=False, default=0)  # 定数
    unit = db.Column(db.String(50), default="個")
    area = db.Column(db.String(100), default="")
    image_path = db.Column(db.String(300), default="")
    supplier = db.Column(db.String(200), default="")  # 発注先
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stock = db.relationship("Stock", backref="item", uselist=False, cascade="all, delete-orphan")
    records = db.relationship("StockRecord", backref="item", cascade="all, delete-orphan", order_by="StockRecord.created_at.desc()")
    orders = db.relationship("Order", backref="item", cascade="all, delete-orphan", order_by="Order.created_at.desc()")

    @property
    def quantity(self):
        return self.stock.quantity if self.stock else 0

    @property
    def status(self):
        qty = self.quantity
        if self.par_level == 0:
            return "normal"
        if qty <= 0:
            return "order"
        if qty <= self.par_level * 0.5:
            return "order"
        if qty <= self.par_level:
            return "low"
        return "normal"

    @property
    def status_label(self):
        labels = {"normal": "正常", "low": "少ない", "order": "発注必要"}
        return labels.get(self.status, "正常")


class Stock(db.Model):
    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockRecord(db.Model):
    __tablename__ = "stock_records"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    record_type = db.Column(db.String(10), nullable=False)  # "in" or "out"
    quantity = db.Column(db.Integer, nullable=False)
    operator = db.Column(db.String(100), default="")
    note = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InventoryCheck(db.Model):
    __tablename__ = "inventory_checks"

    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False)
    checker_name = db.Column(db.String(100), nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(300), default="")

    check_items = db.relationship("InventoryCheckItem", backref="check", cascade="all, delete-orphan", order_by="InventoryCheckItem.id")


class InventoryCheckItem(db.Model):
    __tablename__ = "inventory_check_items"

    id = db.Column(db.Integer, primary_key=True)
    check_id = db.Column(db.Integer, db.ForeignKey("inventory_checks.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    system_quantity = db.Column(db.Integer, nullable=False, default=0)
    actual_quantity = db.Column(db.Integer, nullable=False, default=0)
    difference = db.Column(db.Integer, nullable=False, default=0)

    item = db.relationship("Item")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending / ordered / received
    note = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ordered_at = db.Column(db.DateTime, nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
